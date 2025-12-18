import asyncio
import random
import os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from telethon.tl.types import InputPeerChannel
from telethon.utils import get_peer_id
from telethon import TelegramClient, events, Button
from telethon.tl.types import PeerUser, ChatBannedRights
from telethon.sessions import MemorySession
from telethon.errors import ChatNotModifiedError
from google import genai
from google.genai.errors import APIError
from aiohttp import web

# ==================== CONFIGURAÇÕES ====================
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GRUPO_ID = int(os.getenv("TELEGRAM_GRUPO_ID"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME")

CAMINHO_BANNER_INTERVALO = "fotosbotmvm/bannerencerramento.png"
CAMINHO_BANNER_ENCERRAMENTO = "fotosbotmvm/bannerencerramento2.png"

# ==================== CLIENT (CORRIGIDO PARA O RENDER) ====================

bot = TelegramClient(MemorySession(), API_ID, API_HASH)

# ==================== INICIALIZAÇÃO GEMINI ====================
gemini_client = None
chat_sessions = {}

try:
    if GEMINI_API_KEY != "AIzaSyCjuNRdVM8sk8nsFdHd-8jdaTmFXUtv2X8": # Garante que não use a chave de exemplo
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    else:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Erro ao inicializar o Cliente Gemini: {e}")
    gemini_client = None

copy_conversations = {}

# ==================== FRASES PARA O PRIVADO ====================
frases_privado = [
    "❌ No PV eu sou igual Pixel não instalado: não rastreio nada! 📡 Va lá no grupo e digita /menu!",
    "❌ Aqui no privado minha BM caiu e o suporte do Zuck não responde! 📉 Me chama no grupo com /menu!",
    "❌ Erro de Criativo! 🚩 No privado eu recebi um Shadowban. Digita /menu lá no grupo!",
    "❌ Falar no PV é igual rodar anúncio sem público: não dá conversão! 💸 Vai pro grupo usar o /menu!",
    "❌ Minha Contingência não permite papo no privado hoje! 🛡️ Me aciona no grupo com o /menu!",
    "❌ CBO ativado: foquei todo o meu orçamento no grupo! 💰 Digita /menu lá para falar comigo!",
    "❌ O Facebook me bloqueou no PV por atividade suspeita! 👮‍♂️ Me encontra no grupo usando /menu!",
    "❌ Minha esteira de aquecimento ainda não chegou no PV! 🔥 Me usa no grupo com o /menu!",
    "❌ Público Lookalike detectado no privado: bloqueando acesso! 👤❌ Vá para o grupo e use o /menu!",
    "❌ CPA no privado tá muito alto! 📈 Prefiro converter lá no grupo com o comando /menu!",
    "❌ Minha Landing Page deu 404 no privado! 🚧 Me chama lá no grupo usando o /menu!",
    "❌ Estou em fase de aprendizado no PV e não respondo ninguém! 🧠 Digita /menu lá no grupo!",
    "❌ Minha API de conversão deu erro no PV! 📉 Só funciono no grupo via /menu!"
]

# ==================== PALAVRAS PROIBIDAS ====================
palavras_proibidas = [
"golpe", "golpes", "golp", "g0lpe", "g0lp3", "golp3", "gôlpe", "gôlp3", "g0lpê",
"golpee", "golpess", "goolpe", "goolp", "golpp", "golppe", "g0lpp3", "g0lppê",
"golppp", "golpista", "g0lpista", "golp1", "g0lp1", "g0lpee", "g o l p e", "g. o. l. p. e",
"golpê", "golp3s", "g0lp3s", "g0lpes", "goipe", "guolpe", "golpesinho", "g0lpinh0",
"golpistas", "g0lpistas", "g0lpi", "golpi", "golpissimo", "golpezinho",
"golpé", "g0lpee", "golpee", "golpii", "gôlpis", "golpizão", "golpizao",
"g.o.l.p.e", "g0l", "gol", "g0lpixta", "golpixta", "g0lpaço", "g0lp1nh0", "golp1nho",
"g0lp3$inhos", "v1d30 g0lp3", "c4ixinha", "caixinha g0lpe", "golpar", "g0lpar",
"golpa", "golpamos", "golpou", "g0lpou", "golpeia", "golpeando", "golpiou", "golpao",
"reembolso", "reembols", "reembolzo", "reembolço", "reemb0lso", "r3embolso", "r3embols0",
"rembolso", "r3mbols0", "remb0lso", "reembols0", "reembo", "reemb", "reembolss",
"reembolsar", "reemb0lsar", "r3embolsar", "r3emb0lsar", "reembolsa", "reembolsou", "reembolsam",
"reenbolso", "reemboso", "rebolso", "reembolzu", "r33mbolso", "re3mbolso",
"reembolsament", "r3embolsament0", "reembolsamento", "reembolsamentu",
"dev0lucao", "devolucao", "dev0luçã0", "devolução", "devolva", "devolve", "dev0lv3",
"devolvem", "devolvo", "devolver", "devolveu", "dev0lve",
"recuperar", "r3cuperar", "recup3rar", "r3cuperacão", "recuperação",
"recupera", "recuperei", "recuperou", "recupero", "recuperam", "recuperavel",
"estornar", "estorno", "estorn0", "est0rno", "est0rnar", "est0rn0", "estorna", "estornei", "estornou",
"r33mb0ls0", "r3c0up3r4r", "r3emb0lsam3nto", "r3mbolsar", "d3v0lva",
"reembolz0", "reembols0s", "r3emb0lso",
"dinheiro de volta", "dinheirodev0lta", "dinheiro devolta",
"grana de volta", "grana dev0lta", "dinheir0 de volta", "dinheir0 devolta",
"dinheiro no bolso", "dinheir0 n0 b0ls0", "grana garantida", "receber de volta",
"ter o dinheiro de volta", "quero meu dinheiro", "quero minha grana", "queria meu dinheiro",
"como receber", "como ter de volta", "restituição", "restituicao", "r3stituicao",
"restituir", "restituo", "restituiu", "restituem",
"pegar o dinheiro", "pegar a grana", "pegar de volta", "d1nh3ir0 d3 v0lt4",
"dinheirodev0lt@", "grana devolt@",
"fraude", "fraud", "fr4ude", "fr@ude", "frauud", "fraudd", "fraud3",
"froude", "fraudi", "fr4ud3", "fraudando", "fraudador", "fr4udador", "fr@udador",
"fraudam", "fraudo", "fraudar", "fr4udar", "fraudei", "fraudou", "fr@udar",
"estelionato", "estelion", "estelionat0", "estelionat@", "estelionat0r", "estelionator",
"estelionário", "esteli0nari0", "estelionari0", "estelionarios", "e$telionato",
"estelionar", "estelionando", "esteliona", "estelionou",
"engano", "enganação", "enganacao", "engana", "enganei", "passada pra trás",
"enganado", "enganad0", "enganad@", "enganad0r", "enganam", "engane", "enganar", "enganou", "enganados",
"trapaça", "trapaca", "trapaceiro", "trapacero", "trapeceiro", "tr4pac3iro",
"trapaceado", "trapacead0", "trapacear", "trapaceou", "trapaceiam", "trapaceia",
"lesado", "lezado", "lezad0", "lesad0", "lesão", "lesao", "lesar", "lesou", "lesa",
"falsidade", "falso", "falsos", "falsificacao", "falsifica", "falsificando",
"esquema", "esqu3ma", "esquema ilegal", "esquema ilícito",
"ilicito", "ilícito", "ilegal", "ilegais", "clandestino",
"pirâmide", "piramid3", "esquema de piramide",
"roubo", "r0ubo", "roub0", "roubado", "r0ubado",
"roubei", "roubaram", "r0ubar", "furto", "furt0", "furtado",
"ladrão", "ladrã0", "ladrãozinho", "ladrãozao", "ladrões", "ladr0es", "ladr03s",
"ladragem", "ladrag3m", "ladra", "ladrinha", "ladraria", "ladraria",
"roub", "rouba", "roubam", "robam", "roubar", "rouba3", "r0uba", "r0ubar",
"r0ubam", "roubando", "roubou", "roub0u", "r0ubou", "robou", "roba", "r0bam",
"furtei", "furtar", "furta", "furtou", "furtando", "furtam", "furtoz", "furtou",
"caiu no conto", "caiu no golpe", "levou o golpe", "passar a perna", "conto do vigário",
"fr@ud3", "est3lionat0", "tr4pacead0", "eng@nad0", "fr4ud4d0r", "e$t3l10n4t0",
"tr4p4c4", "l3$ad0", "fr4udul3nto", "r0ub4d0", "fr4ud3nt0", "fr4udulenta", "est3lion4rio",
"gplpe", "goplpe", "g0plpe", "gp1pe",
"gope", "g0pe", "gop3", "gop", "gopp",
"mentira", "m3ntira", "m3ntir4", "mentir4", "m3ntir", "mentir", "mentiira", "mentiras", "m3ntiras",
"desistir", "d3sistir", "d3sist1r", "desist1r", "d3sist", "desist",
"disisto", "d1sisto", "d1sist0", "disist0",
"diesato", "d1esat0", "d1esato", "diesat0",
"go1pe", "gorpe", "gorpe2", "g0lpe2", "go1p3", "g0lpii", "golep", "goulpe", "golpex", "gople", "g0ple", "g0lpão", "g0lpzão",
"m3ntirã", "m3nt1ra", "m3nt1r4", "mnetira", "mentirz",
"d3sistiu", "d3sisto", "desistiu", "d1esatoo", "ab4ndono", "abandono", "abandonar", "l4rgar", "largar", "larguei"
]

# ==================== FUNÇÃO — LISTAR MEMBROS POR DATA DE ENTRADA ====================
async def listar_membros_com_data():
    participantes = await bot.get_participants(GRUPO_ID, aggressive=True)
    lista = []

    for p in participantes:
        try:
            member = await bot.get_permissions(GRUPO_ID, p.id)
            if hasattr(member.participant, "date") and member.participant.date:
                data_entrada = member.participant.date
            else:
                data_entrada = None

            lista.append({
                "nome": p.first_name or "Sem nome",
                "username": f"@{p.username}" if p.username else "",
                "data": data_entrada
            })
        except Exception:
            pass

    lista_ordenada = sorted(lista, key=lambda x: (x["data"] is None, x["data"]))

    texto = "📅 *Membros por ordem de entrada no grupo:*\n\n"
    for item in lista_ordenada:
        data_formatada = item["data"].strftime("%d/%m/%Y") if item["data"] else "❓ Desconhecida"
        texto += f"• {item['nome']} {item['username']} — entrou em **{data_formatada}**\n"

    return texto

# ==================== FUNÇÃO AUXILIAR PARA TÓPICOS (VERSÃO DEFINITIVA) ====================
async def respond_in_thread(event, texto):
    try:
        chat_id = event.chat_id
        
        msg = await event.get_message() if hasattr(event, 'get_message') else getattr(event, 'message', None)

        thread_id = None
        if msg and msg.reply_to:
            thread_id = msg.reply_to.reply_to_top_id or msg.reply_to_msg_id

        limite = 4000
        partes = [texto[i:i+limite] for i in range(0, len(texto), limite)] if len(texto) > limite else [texto]
        
        for parte in partes:
            await event.client.send_message(
                chat_id, 
                parte, 
                parse_mode="markdown", 
                reply_to=thread_id
            )
            
    except Exception as e:
        print(f"❌ Erro na função respond_in_thread: {e}")

# --- FUNÇÕES AUXILIARES ACIMA ---

# ==================== /menu — MENU INICIAL COM BOTÕES ====================
@bot.on(events.NewMessage(pattern=r'/menu'))
async def menu_handler(event):
    
    if event.is_private:
        raise events.StopPropagation

    buttons = [
        [Button.inline("📋 Listar Membros (admin)", b"listar")],
        [Button.inline("🎲 Sorteio (admin)", b"sorteio")],
        [Button.inline("ℹ Consultar Informações de usuários (admin)", b"info")],
        [Button.inline("📄 Exportar Membros (admin)", b"exportar")]
    ]
    
    if gemini_client:
        buttons.append([Button.inline("🤖 Use /gemini (texto) para falar com o gemini", b"gemini")])
        buttons.append([Button.inline("🔥 Gerar Copy Ads com Gemini", b"gerar_copy")])
        buttons.append([Button.inline("💬 Gerar Texto de Remarketing (X1)", b"gerar_remarketing")])
        
    await event.respond(
        "👋 *Olá! Escolha uma função abaixo:*",
        buttons=buttons,
        parse_mode="markdown",
        reply_to=event.message.id
    )
    
    raise events.StopPropagation

# ==================== BOTÃO: LISTAR MEMBROS (RESTRITO A ADMIN) ====================
@bot.on(events.CallbackQuery(data=b"listar"))
async def listar_callback(event):
    chat_id = event.chat_id
    user_id = event.sender_id
    
    # 🛑 VERIFICAÇÃO DE ADMIN 🛑
    if not await is_admin(event, chat_id, user_id):
        await event.answer("🚫 Somente administradores podem listar membros.", alert=True)
        return
    # --------------------------
    
    await event.edit("⏳ Buscando membros e datas de entrada...")
    texto = await listar_membros_com_data()
    await respond_in_thread(event, texto)

# ==================== BOTÃO: SORTEIO (RESTRITO A ADMIN) ====================
@bot.on(events.CallbackQuery(data=b"sorteio"))
async def sorteio_callback(event):
    chat_id = event.chat_id
    user_id = event.sender_id
    
    # 🛑 VERIFICAÇÃO DE ADMIN 🛑
    if not await is_admin(event, chat_id, user_id):
        await event.answer("🚫 Somente administradores podem realizar sorteios.", alert=True)
        return
    # --------------------------
    
    await event.edit("🎲 Sorteando um membro do grupo...")
    membras = await bot.get_participants(GRUPO_ID)
    if not membras:
        return await respond_in_thread(event, "⚠️ Não encontrei membros no grupo.")

    sorteado = random.choice(membras)
    nome = sorteado.first_name or "Usuário sem nome"
    user = f"@{sorteado.username}" if sorteado.username else "(sem username)"

    resposta = (
        f"🎉 *SORTEIO REALIZADO!*\n\n"
        f"👤 **Vencedor:** {nome} {user}"
    )

    await respond_in_thread(event, resposta)

# ==================== BOTÃO: INFO → PEDIR MENÇÃO (RESTRITO A ADMIN) ====================
@bot.on(events.CallbackQuery(data=b"info"))
async def info_callback(event):
    chat_id = event.chat_id
    user_id = event.sender_id
    
    # 🛑 VERIFICAÇÃO DE ADMIN 🛑
    if not await is_admin(event, chat_id, user_id):
        await event.answer("🚫 Somente administradores podem acessar a função de consulta de info pelo menu.", alert=True)
        return
    # --------------------------
    
    await event.answer()
    mensagem = (
        "ℹ *Consultar Informações de Usuário*\n\n"
        "Envie o comando `/info` no grupo mencionando o usuário com @ ou responda a mensagem dele.\n\n"
        "👉 Exemplo: `/info @username`"
    )
    
    await event.edit(mensagem, parse_mode="markdown")

# ==================== BOTÃO: EXPORTAR MEMBROS PARA ARQUIVO (RESTRITO A ADMIN) ====================
@bot.on(events.CallbackQuery(data=b"exportar"))
async def exportar_callback(event):
    chat_id = event.chat_id
    user_id = event.sender_id

    # 🛑 VERIFICAÇÃO DE ADMIN 🛑
    if not await is_admin(event, chat_id, user_id):
        await event.answer("🚫 Somente administradores podem exportar membros.", alert=True)
        return
    # --------------------------
    
    await event.edit("⏳ Gerando arquivo com todos os membros...")

    participantes = await bot.get_participants(GRUPO_ID, aggressive=True)

    linhas = ["Nome | Username | ID | Data de Entrada"]
    for p in participantes:
        nome = p.first_name or "Sem nome"
        username = f"@{p.username}" if p.username else "(sem username)"
        user_id = p.id
        
        data_entrada = "❓ Desconhecida"
        try:
            member = await bot.get_permissions(GRUPO_ID, p.id)
            if hasattr(member.participant, 'date') and member.participant.date:
                data_entrada = member.participant.date.strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            pass 

        linhas.append(f"{nome} | {username} | {user_id} | {data_entrada}")

    conteudo = "\n".join(linhas)

    nome_arquivo = f"membros_{datetime.now().strftime('%d-%m-%Y')}.txt"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(conteudo)

    await bot.send_file(event.chat_id, nome_arquivo, caption="📄 Lista completa de membros do grupo")
    
    if os.path.exists(nome_arquivo):
        os.remove(nome_arquivo)

# ==================== BOTÃO: GEMINI (INSTRUÇÃO) CORRIGIDO ====================
@bot.on(events.CallbackQuery(data=b"gemini"))
async def gemini_callback_instrucao(event):
    await event.answer() 
    
    if not gemini_client:
        
        await respond_in_thread(event, "❌ O serviço Gemini não está configurado. Verifique a chave de API no código.")
        return

    instrucao = (
        "🤖 *Como usar o Gemini:*\n\n"
        "Basta usar o comando `/gemini` seguido da sua pergunta *no grupo*. "
        "O Gemini lembrará do contexto de suas perguntas anteriores nesta conversa."
        "\n\nExemplo: `/gemini Me explique sobre Tráfego Pago`"
        "\n\n⚠AVISO: O gemini no telegram tem limite de uso diário, caso apareça um texto de erro é porque excedeu o limite."
    )
    
    
    await respond_in_thread(event, instrucao)
    
# ==================== BOTÃO: GERAR COPY ADS ====================
# Este handler é para ABRIR o fluxo de conversação
@bot.on(events.CallbackQuery(data=b"gerar_copy"))
async def iniciar_geracao_copy_callback(event):
    if not gemini_client:
        return await event.edit("❌ O serviço Gemini não está configurado.")

    
    await event.edit("🤖 *GERADOR DE COPY ADS (Gemini)*\n\nVamos começar. Por favor, digite o **NOME DA LOJA**:", parse_mode="markdown")
    
    
    key = (event.sender_id, event.chat_id)
    copy_conversations[key] = {"step": 1, "type": "copy", "data": {}} # Adiciona 'type'
    
    
    raise events.StopPropagation

# -------------------- BOTÃO: GERAR REMARKETING --------------------
@bot.on(events.CallbackQuery(data=b'gerar_remarketing'))
async def callback_gerar_remarketing(event):
    if not gemini_client:
        await event.answer("⚠️ O cliente Gemini não está configurado. Verifique a chave API.", alert=True)
        return

    chat_id = event.chat_id
    user_id = event.sender_id
    # Padroniza a chave (sender_id, chat_id)
    key = (user_id, chat_id)

    if key in copy_conversations:
        await event.answer("⚠️ Você já tem uma conversa em andamento. Termine ou use `/cancelar`.", alert=True)
        return

    # Passo 1: Solicitar o nicho da loja
    copy_conversations[key] = {
        "step": 1,
        "type": "remarketing", # Identificador para o handler de mensagens
        "data": {}
    }

    await event.edit(
        "💬 *Gerador de Texto de Remarketing (X1)*\n\n"
        "👉 **Passo 1 de 4:** Qual é o **nicho** da sua loja (Ex: Moda Feminina, Eletrônicos, Pets)?",
        parse_mode="markdown"
    )

    raise events.StopPropagation
    
# ==================== COMANDO: /info @usuario (informações do usuário) (RESTRITO A ADMIN) ====================
@bot.on(events.NewMessage(pattern=r'/info'))
async def consultar_info_comando(event):
    if event.is_private:
        return
    
    chat_id = event.chat_id
    user_id = event.sender_id
    
    # 🛑 VERIFICAÇÃO DE ADMIN 🛑
    if not await is_admin(event, chat_id, user_id):
        await event.reply("🚫 Somente administradores podem usar o comando `/info`.", reply_to=event.message.id)
        return
    # --------------------------
    
    mencao_id = None
    if event.message.entities:
        for ent in event.message.entities:
            
            if hasattr(ent, "user_id") and ent.user_id:
                mencao_id = ent.user_id
                break
    
    
    if not mencao_id and event.reply_to_msg_id:
        try:
            replied_msg = await event.get_reply_message()
            if replied_msg and replied_msg.sender_id:
                mencao_id = replied_msg.sender_id
        except:
            pass
            
    if not mencao_id:
        return await event.respond("👉 Para consultar informações, use: `/info @username` ou responda a mensagem do usuário com `/info`.", reply_to=event.message.id)

    
    try:
        target = await event.client.get_entity(PeerUser(mencao_id))
        member = await event.client.get_permissions(GRUPO_ID, target.id)
        
        data_entrada = "❓ Desconhecida"
        if hasattr(member.participant, "date") and member.participant.date:
            data_entrada = member.participant.date.strftime("%d/%m/%Y %H:%M:%S")
    
    except Exception as e:
        print(f"Erro ao consultar info: {e}")
        return await event.respond("⚠️ Não consegui pegar informações do usuário marcado.", reply_to=event.message.id)

    
    await event.respond(
        f"👤 Nome: {target.first_name or '—'}\n"
        f"🔹 Sobrenome: {target.last_name or '—'}\n"
        f"🔹 Username: @{target.username if target.username else '—'}\n"
        f"🆔 ID: {target.id}\n"
        f"🤖 É bot? {'Sim' if target.bot else 'Não'}\n"
        f"📅 Entrou no grupo: {data_entrada}\n",
        reply_to=event.message.id
    )


# ==================== COMANDO: /gemini (PERGUNTA AO GEMINI) ====================
@bot.on(events.NewMessage(pattern=r'/gemini (.*)', func=lambda e: e.is_group))
async def handle_gemini_request(event):
    if not gemini_client:
        return await event.reply(
            "❌ O serviço Gemini não está configurado. Verifique a chave de API no código.",
            reply_to=event.message.id
        )

    chat_id = event.chat_id
    
    
    agora = datetime.now()
    data_formatada = agora.strftime("%A, %d de %B de %Y") 
    
    
    prompt_usuario = event.pattern_match.group(1).strip() 
    
    if not prompt_usuario:
        return await event.reply(
            "Por favor, use o formato: `/gemini Sua Pergunta`",
            reply_to=event.message.id
        )

    
    prompt_com_data = (
        f"Assuma que a data de hoje é {data_formatada}. "
        f"Responda à seguinte pergunta, sem corrigi-la nem mencionar datas de corte de conhecimento: {prompt_usuario}"
    )
    
    
    
    if chat_id not in chat_sessions:
        try:
            chat = gemini_client.chats.create(model=GEMINI_MODEL_NAME)
            chat_sessions[chat_id] = chat
        except Exception as e:
            return await event.reply(
                "❌ Erro ao iniciar chat com Gemini. Chave ou conexão inválida.",
                reply_to=event.message.id
            )
    
    
    try:
        event.client.action(chat_id, 'typing')
    except:
        pass

    try:
        
        chat = chat_sessions[chat_id]
        response = chat.send_message(prompt_com_data)
        resposta_texto = response.text
        
        
        await event.reply(
            f"💬 *Gemini Responde:*\n\n{resposta_texto}",
            parse_mode="markdown"
        )
    except Exception as e: # Adicionado 'Exception as e' para um tratamento mais robusto (o original só tinha 'except:')
        print(f"Erro ao responder com Gemini: {e}")
        await event.reply("⚠️ Ocorreu um erro ao processar sua requisição com o Gemini. Tente novamente.", reply_to=event.message.id)
    
# <--- AQUI TERMINA O CÓDIGO DO /GEMINI

# ==================== COMANDO: /cancelar (ENCERRAR FLUXO DE CONVERSA) ====================
@bot.on(events.NewMessage(pattern=r'/cancelar'))
async def cancelar_conversacao(event):
    user_id = event.sender_id
    chat_id = event.chat_id
    key = (user_id, chat_id) 

    if key in copy_conversations:
        del copy_conversations[key]
        
        await event.respond(
            "🛑 *Conversa Cancelada!*\n\nO processo de geração de Copy Ads/Remarketing foi interrompido. "
            "Use `/menu` para começar um novo processo.",
            parse_mode="markdown",
            reply_to=event.message.id
        )
    else:
        await event.respond(
            "ℹ️ *Nenhuma conversa ativa para cancelar.*",
            parse_mode="markdown",
            reply_to=event.message.id
        )
    
    # IMPORTANTE: Garante que o evento pare aqui e não passe para collect_copy_data
    raise events.StopPropagation


# ==================== FUNÇÃO DE CONVERSA PARA GERAR COPY (STEPS) E REMARKETING (CORRIGIDO) ====================
@bot.on(events.NewMessage(func=lambda e: (e.sender_id, e.chat_id) in copy_conversations and not e.raw_text.startswith('/')))
async def collect_copy_data(event):
    user_id = event.sender_id
    chat_id = event.chat_id
    # Chave padronizada: (user_id, chat_id)
    key = (user_id, chat_id) 
    
    
    if key not in copy_conversations:
        return

    conv_data = copy_conversations[key]
    step = conv_data["step"]
    user_input = event.raw_text.strip()
    
    # -------------------- FLUXO GERAR REMARKETING X1 --------------------
    if conv_data.get("type") == "remarketing":
        
        # -------------------- PASSO 1: COLETA NICHO --------------------
        if step == 1:
            if not user_input or len(user_input.strip()) < 3:
                await event.respond("⚠️ Por favor, insira o **nicho** de forma clara.", reply_to=event.message.id)
                conv_data["step"] = 1 # Repete
                raise events.StopPropagation # Adicionado StopPropagation
            
            conv_data["data"]["NICHO"] = user_input.strip()
            conv_data["step"] = 2
            await event.respond(
                "✅ Nicho Salvo.\n\n"
                "👉 **Passo 2 de 4:** Qual é o **Nome do Produto** ou **Serviço** que você quer fazer o remarketing? (Ex: Tênis Esportivo, Curso de Marketing)",
                parse_mode="markdown",
                reply_to=event.message.id
            )

        # -------------------- PASSO 2: COLETA PRODUTO --------------------
        elif step == 2:
            if not user_input or len(user_input.strip()) < 3:
                await event.respond("⚠️ Por favor, insira o **Nome do Produto/Serviço** de forma clara.", reply_to=event.message.id)
                conv_data["step"] = 2 # Repete
                raise events.StopPropagation
            
            conv_data["data"]["PRODUTO"] = user_input.strip()
            conv_data["step"] = 3
            await event.respond(
                "✅ Produto Salvo.\n\n"
                "👉 **Passo 3 de 4:** Qual é o **Motivo principal** pelo qual o cliente parou de comprar? (Ex: Abandonou o carrinho, Pediu desconto e sumiu, Não respondeu a primeira mensagem)",
                parse_mode="markdown",
                reply_to=event.message.id
            )

        # -------------------- PASSO 3: COLETA MOTIVO --------------------
        elif step == 3:
            if not user_input or len(user_input.strip()) < 5:
                await event.respond("⚠️ Por favor, descreva o **Motivo** de forma clara (min. 5 letras).", reply_to=event.message.id)
                conv_data["step"] = 3 # Repete
                raise events.StopPropagation
            
            conv_data["data"]["MOTIVO"] = user_input.strip()
            conv_data["step"] = 4
            await event.respond(
                "✅ Motivo Salvo.\n\n"
                "👉 **Passo 4 de 4:** Qual é o **Benefício** ou **Oferta** que você vai apresentar agora para o cliente retomar a compra? (Ex: 10% OFF, Frete Grátis, Brinde Exclusivo)",
                parse_mode="markdown",
                reply_to=event.message.id
            )

        # -------------------- PASSO 4: COLETA OFERTA E GERA O TEXTO --------------------
        elif step == 4:
            if not user_input or len(user_input.strip()) < 5:
                await event.respond("⚠️ Por favor, insira a **Oferta/Benefício** de forma clara (min. 5 letras).", reply_to=event.message.id)
                conv_data["step"] = 4 # Repete
                raise events.StopPropagation
            
            conv_data["data"]["OFERTA"] = user_input.strip()

            processing_msg = await event.respond("⏳ Ótimo! Enviando dados para o Gemini... *Aguarde alguns segundos.*", reply_to=event.message.id)
            
            data = conv_data["data"]
            
            final_prompt = (
                f"Você é um Copywriter especialista em remarketing e recuperação de clientes no WhatsApp (X1). "
                f"Sua única tarefa é gerar o texto curto de remarketing. NÃO inclua títulos, descrições, ou hashtags, Apenas o corpo da mensagem. "
                f"Gere um texto persuasivo e empático, focado na recuperação, para um cliente que demonstrou interesse no produto '{data['PRODUTO']}' do nicho '{data['NICHO']}'. "
                f"O motivo do remarketing é: '{data['MOTIVO']}'. "
                f"O objetivo do texto é apresentar o seguinte benefício/oferta: '{data['OFERTA']}'. "
                f"A mensagem deve ser amigável, direta e usar emojis. O cliente deve se sentir valorizado e motivado a fechar a compra *agora*. "
                f"O texto deve ser curto e ideal para envio imediato no WhatsApp (X1)."
            )

            try:
                
                event.client.action(chat_id, 'typing') 
                
                if not gemini_client:
                    raise Exception("Cliente Gemini não inicializado.")

                
                remarketing_chat = gemini_client.chats.create(model=GEMINI_MODEL_NAME) 
                response = remarketing_chat.send_message(final_prompt)
                
                
                await event.client.send_message(
                    chat_id, 
                    f"💬 *Texto de Remarketing (X1) Gerado pelo Gemini:*\n\n{response.text}",
                    parse_mode="markdown",
                    reply_to=processing_msg.id
                )
            
            
            except APIError as api_e:
                print(f"ERRO FATAL GEMINI API: {api_e}") 
                
                if "503 UNAVAILABLE" in str(api_e):
                    error_message = (
                        "⚠️ *SOBRECARGA DO SERVIDOR GEMINI (503) | TENTE NOVAMENTE!*\n\n"
                        "O servidor da IA está temporariamente sobrecarregado. Por favor, tente gerar o texto novamente em alguns minutos."
                    )
                elif "429 Quota exceeded" in str(api_e):
                    error_message = (
                        "❌ *LIMITE DIÁRIO EXCEDIDO (429) | GEMINI*\n\n"
                        "Você atingiu o limite de uso diário da API do Gemini. A função estará inativa até amanhã."
                    )
                else:
                    error_message = (
                        "❌ *ERRO NA API DO GEMINI!*\n\n"
                        "Ocorreu um erro desconhecido na comunicação com a API.\n\n"
                        f"Código de Erro: `{api_e}`"
                    )

                await event.client.send_message(chat_id, error_message, parse_mode="markdown", reply_to=processing_msg.id)

            
            except Exception as e:
                error_message = (
                    "❌ Ocorreu um erro desconhecido ao gerar o texto de remarketing.\n\n"
                    f"Detalhes Técnicos: `{e}`"
                )
                print(f"ERRO GEMINI GENÉRICO: {e}") 
                await event.client.send_message(chat_id, error_message, parse_mode="markdown", reply_to=processing_msg.id)

            # Fim do Fluxo, Limpa a Conversa
            del copy_conversations[key]
        
        # Garante que, se for remarketing, não passe para o fluxo de Copy Ads abaixo.
        raise events.StopPropagation 
        
    # -------------------- STEPS DE COLETA DE DADOS (COPY ADS ORIGINAL) --------------------
    
    # Este bloco só será executado se conv_data.get("type") NÃO for "remarketing",
    # o que acontece no fluxo original de Copy Ads onde 'type' não é definido (ou é definido como 'copy' no código corrigido acima).
    try:
        if step == 1:
            conv_data["data"]["NOME_LOJA"] = user_input
            conv_data["step"] = 2
            await event.respond("Certo! Agora, qual é o **NICHO** (ex: Roupas Femininas, Produtos de Limpeza, Acessórios de Pet):", reply_to=event.message.id)
            
        elif step == 2:
            conv_data["data"]["NICHO"] = user_input
            conv_data["step"] = 3
            await event.respond("A loja vende no **VAREJO ou ATACADO**? (Digite 'Varejo' ou 'Atacado'):", reply_to=event.message.id)
            
        elif step == 3:
            conv_data["data"]["TIPO_VENDA"] = user_input
            conv_data["step"] = 4
            await event.respond("O envio é para qual região? (Digite: **CIDADES/REGIÕES, ESTADO, BRASIL**):", reply_to=event.message.id)

        elif step == 4:
            conv_data["data"]["ENVIO"] = user_input
            conv_data["step"] = 5
            await event.respond("Quais são as **FORMAS DE PAGAMENTO**? (Ex: PIX, Cartão, Boleto):", reply_to=event.message.id)

        elif step == 5:
            conv_data["data"]["PAGAMENTO"] = user_input
            conv_data["step"] = 6
            await event.respond("O direcionamento do anúncio é para onde? (Ex: **Página do Instagram, Conversa no Instagram, Conversa no WhatsApp, Site**):", reply_to=event.message.id)

        # -------------------- PASSO 6: COLETA DIRECIONAMENTO E PASSA PARA O 7 --------------------
        elif step == 6:
            conv_data["data"]["DIRECIONAMENTO"] = user_input
            conv_data["step"] = 7
            await event.respond("Perfeito! Gostaria de adicionar alguma **OBSERVAÇÃO** extra para a Copy (Ex: *Super Promoção de Inverno*, *Oferta Imperdível*, ou digite **NEGAR** para pular):", reply_to=event.message.id)
            
        # -------------------- PASSO 7: COLETA OBSERVAÇÃO E GERA A COPY --------------------
        elif step == 7:
            user_input_upper = user_input.strip().upper()
            
            if user_input_upper in ["NEGAR", "PULAR", "NAO", "NÃO", "-"]:
                conv_data["data"]["OBSERVACAO"] = ""
    
            else:
                conv_data["data"]["OBSERVACAO"] = user_input
            
            
            processing_msg = await event.respond("⏳ Ótimo! Enviando dados para o Gemini... *Aguarde alguns segundos.*", reply_to=event.message.id)
            
            data = conv_data["data"]
            
            
            observacao_text = data.get('OBSERVACAO', '').strip()
            observacao_prompt = (
                f" **INCLUA A SEGUINTE OBSERVAÇÃO/OFERTA:** {observacao_text}. Garanta que essa observação seja o ponto principal de Atenção da sua AIDA."
                if observacao_text else 
                ""
            )

            final_prompt = (
                f"Você é um Copywriter de alta performance para Facebook Ads. "
                f"Sua única tarefa é gerar o texto da copy. NÃO inclua títulos, descrições, ou hashtags, Apenas o corpo da copy. "
                f"Faça uma copy persuasiva e criativa para Facebook Ads para a loja \"{data['NOME_LOJA']}\" "
                f"que vende: {data['NICHO']}, no regime de {data['TIPO_VENDA']}. "
                f"O envio é para {data['ENVIO']}. "
                f"As Formas de pagamento aceitas são: {data['PAGAMENTO']}. "
                f"A chamada para ação (CTA) deve direcionar o cliente para: {data['DIRECIONAMENTO']}."
                f"{observacao_prompt}" 
                f"Faça a COPY seguindo o modelo AIDA (Atenção, Interesse, Desejo, Ação). A copy deve ser pequena e resumida. Use emojis e quebras de linha para destacar."
            )

            
            try:
                
                event.client.action(chat_id, 'typing') 
                
                if not gemini_client:
                    
                    raise Exception("Cliente Gemini não inicializado.")

                
                copy_chat = gemini_client.chats.create(model=GEMINI_MODEL_NAME) 
                response = copy_chat.send_message(final_prompt)
                
                await event.client.send_message(
                    chat_id, 
                    f"✨ *Copy Gerada pelo Gemini para {data['NOME_LOJA']}:*\n\n{response.text}",
                    parse_mode="markdown",
                    reply_to=processing_msg.id
                )
            
            
            except APIError as api_e:
                print(f"ERRO FATAL GEMINI API: {api_e}") 
                
                if "503 UNAVAILABLE" in str(api_e):
                    error_message = (
                        "⚠️ *SOBRECARGA DO SERVIDOR GEMINI (503) | TENTE NOVAMENTE!*\n\n"
                        "O servidor da IA está temporariamente sobrecarregado. Por favor, tente gerar a copy novamente em alguns minutos."
                    )
                elif "429 Quota exceeded" in str(api_e):
                    error_message = (
                        "❌ *LIMITE DIÁRIO EXCEDIDO (429) | GEMINI*\n\n"
                        "Você atingiu o limite de uso diário da API do Gemini. A função estará inativa até amanhã."
                    )
                else:
                    error_message = (
                        "❌ *ERRO NA API DO GEMINI!*\n\n"
                        "Ocorreu um erro desconhecido na comunicação com a API.\n\n"
                        f"Código de Erro: `{api_e}`"
                    )

                await event.client.send_message(chat_id, error_message, parse_mode="markdown", reply_to=processing_msg.id)

            
            except Exception as e:
                error_message = (
                    "❌ Ocorreu um erro desconhecido ao gerar a copy.\n\n"
                    f"Detalhes Técnicos: `{e}`"
                )
                print(f"ERRO GEMINI GENÉRICO: {e}") 
                await event.client.send_message(chat_id, error_message, parse_mode="markdown", reply_to=processing_msg.id)

            
            del copy_conversations[key]
            
    except Exception as e:
        
        print(f"Erro na coleta de dados da copy/remarketing (Lógica): {e}")
        await event.respond("❌ Desculpe, ocorreu um erro inesperado. Tente novamente ou use o `/menu`.", reply_to=event.message.id)
        if key in copy_conversations:
            del copy_conversations[key]
    
    
    raise events.StopPropagation

# ==================== FUNÇÃO HORÁRIO PERMITIDO ====================
def horario_permitido():
    
    fuso_horario = ZoneInfo("America/Sao_Paulo") 
    agora = datetime.now(fuso_horario).time()
    inicio_manha = time(9, 0)
    fim_manha = time(11, 30)
    inicio_tarde = time(12, 40)
    fim_tarde = time(22, 0)
    
    
    return (inicio_manha <= agora <= fim_manha) or (inicio_tarde <= agora <= fim_tarde)

# ==================== CAPTURA DE MENSAGENS — BLOQUEIO DO PRIVADO, HORÁRIO E PALAVRAS ====================
@bot.on(events.NewMessage(incoming=True))
async def tratar_info(event):
    
    if event.out:
        return

    key = (event.sender_id, event.chat_id)
    if key in copy_conversations:
        return 

    if event.is_private:
        await event.respond(random.choice(frases_privado), reply_to=event.message.id)
        raise events.StopPropagation

    if event.raw_text and event.raw_text.startswith("/"):
        return

    if event.raw_text:
        texto_msg = event.raw_text.lower()
        texto_normalizado = texto_msg.replace(" ", "").replace(".", "")

        for palavra in palavras_proibidas:
            palavra_normalizada = palavra.lower().replace(" ", "").replace(".", "")
            if palavra_normalizada in texto_normalizado:
                user = None
                try:
                    user = await event.get_sender()
                except:
                    pass
                
                agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                user_info = f"{user.first_name} (ID: {user.id})" if user else "Desconhecido"
                
                print(f"🚨 MENSAGEM BANIDA: {user_info} enviou '{palavra}'")
                
                try:
                    await event.delete()
                except Exception as delete_e:
                    print(f"Falha ao deletar: {delete_e}")
                return
                
# ==================== TAREFA DE MONITORAMENTO — BLOQUEIO E AVISO ====================
async def monitorar_horario():
    bloqueado = None
    
    TOPICOS_PARA_AVISAR = [1, 2561] #

    inicio_manha = time(9, 0)
    fim_manha = time(11, 30)
    inicio_tarde = time(12, 40)
    fim_tarde = time(22, 0)

    while True:
        try:
            fuso_horario = ZoneInfo("America/Sao_Paulo")
            agora = datetime.now(fuso_horario).time()
            
            permitido = (inicio_manha <= agora <= fim_manha) or (inicio_tarde <= agora <= fim_tarde)

            if permitido and bloqueado is not False:
                try:
                    await bot.edit_permissions(GRUPO_ID, send_messages=True, view_messages=True)
                    
                    for tid in TOPICOS_PARA_AVISAR:
                        await bot.send_message(GRUPO_ID, "🔓 **GRUPO ABERTO!**\n\nMensagens permitidas a partir de agora! 🚀", reply_to=tid)
                except ChatNotModifiedError:
                    pass
                bloqueado = False

            elif not permitido and bloqueado is not True:
                try:
                    await bot.edit_permissions(GRUPO_ID, send_messages=False, view_messages=True)
                    
                    msg_fechamento = ""
                    banner_a_enviar = None

                    if fim_manha < agora < inicio_tarde:
                        banner_a_enviar = CAMINHO_BANNER_INTERVALO
                        msg_fechamento = "🍽️ **Pausa para o almoço!**\n\nVoltamos às 12:40 ⏰\nAté já! 😄"
                    elif agora > fim_tarde or agora < inicio_manha:
                        banner_a_enviar = CAMINHO_BANNER_ENCERRAMENTO
                        msg_fechamento = "🌙 **Suporte encerrado!**\n\nRetornamos amanhã às 9:00 ⏰\nBom descanso! 😊"

                    for tid in TOPICOS_PARA_AVISAR:
                        if msg_fechamento:
                            await bot.send_message(GRUPO_ID, msg_fechamento, reply_to=tid)
                        if banner_a_enviar and os.path.exists(banner_a_enviar):
                            await bot.send_file(GRUPO_ID, banner_a_enviar, reply_to=tid)
                            
                except ChatNotModifiedError:
                    pass
                bloqueado = True

        except Exception as e:
            print(f"❌ Erro crítico no monitoramento: {e}")

        await asyncio.sleep(30)
        
# ==================== MONITORAMENTO DE PALAVRAS PROIBIDAS ====================
@bot.on(events.NewMessage(func=lambda e: e.is_group))
async def filtro_palavras(event):

    if await is_admin(event, event.chat_id, event.sender_id):
        return

    frase_completa = event.raw_text
    texto_minusculo = frase_completa.lower()
    
    for palavra in palavras_proibidas:
        if palavra in texto_minusculo:
            user = await event.get_sender()
            nome_usuario = user.first_name if user else "Desconhecido"
            
            print(f"🚫 LOG MVM: Termo '{palavra}' detectado!")
            print(f"👤 Usuário: {nome_usuario} ({event.sender_id})")
            print(f"📝 Mensagem enviada: {frase_completa}")
            print("-" * 30)
            
            try:
                await event.delete()
            except Exception as e:
                print(f"⚠️ Erro ao tentar apagar mensagem: {e}")
            break 
            
# ==================== SERVIDOR WEB PARA O RENDER ====================
async def iniciar_servidor_web():
    """Mantém o Render feliz abrindo uma porta HTTP obrigatória."""
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot is running"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"✅ Servidor Web monitorando porta: {port}")
    
# ==================== FUNÇÃO PRINCIPAL ====================
async def main():
    print("Iniciando componentes...")
    
    await bot.start(bot_token=TOKEN)
    print("✅ Bot conectado ao Telegram!")

    asyncio.create_task(iniciar_servidor_web())
    asyncio.create_task(monitorar_horario())

    try:
        print(f"Buscando acesso ao grupo {GRUPO_ID}...")
        await bot.get_entity(GRUPO_ID)
        print("✅ Grupo reconhecido com sucesso!")
    except Exception as e:
        print(f"⚠️ Aviso: Grupo ainda não resolvido: {e}")

    print("🚀 BOT INICIADO E ESCUTANDO MENSAGENS!")
    
    await bot.run_until_disconnected()

# ==================== EXECUÇÃO ====================
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Bot desligado.")










