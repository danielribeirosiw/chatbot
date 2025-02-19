import logging
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

# Configuração do Logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Tokens e URLs (Use variáveis de ambiente para segurança)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_URL = "https://api.themoviedb.org/3/discover/movie"
TMDB_IMG_URL = "https://image.tmdb.org/t/p/w500"
PROVIDERS_URL = "https://api.themoviedb.org/3/movie/{}/watch/providers"

# Fases da conversa
TERMS, RECOMMEND = range(2)

# Mensagem dos Termos
TERMS_TEXT = """
🔹 **Termos de Uso do CDB - Database for Movie Lovers!** 🔹

1️⃣ Este bot fornece recomendações de filmes com base no que você disser.  
2️⃣ As informações vêm de bancos de dados públicos e podem não estar 100% corretas.  
3️⃣ Ao usar este bot, você concorda que é apenas para entretenimento.  

✅ Se concorda, digite **"Aceito"** para continuar.
"""

def buscar_filme_por_genero(genero):
    genero_map = {"ação": 28, "comédia": 35, "drama": 18, "terror": 27, "romance": 10749}
    genero_id = genero_map.get(genero.lower())
    
    if not genero_id:
        return None, None, None, None
    
    params = {"api_key": TMDB_API_KEY, "with_genres": genero_id, "language": "pt-BR", "sort_by": "popularity.desc"}
    response = requests.get(TMDB_URL, params=params)
    data = response.json()
    
    if data["results"]:
        filme = data["results"][0]
        titulo = filme.get("title", "Título desconhecido")
        descricao = filme.get("overview", "Sem descrição disponível.")
        poster_path = filme.get("poster_path", "")
        poster_url = TMDB_IMG_URL + poster_path if poster_path else ""
        movie_id = filme.get("id")
        return titulo, descricao, poster_url, movie_id
    return None, None, None, None

async def start(update: Update, context: CallbackContext) -> int:
    user_first_name = update.message.from_user.first_name
    await update.message.reply_text(
        f"Olá, {user_first_name}! 👋\n"
        "Eu sou **CDB - Database for Movie Lovers!** 🎬\n"
        "Antes de começarmos, preciso que você leia e aceite os termos de uso. 📜\n\n"
        + TERMS_TEXT
    )
    return TERMS

async def accept_terms(update: Update, context: CallbackContext) -> int:
    text = update.message.text.lower()
    if "aceito" in text:
        await update.message.reply_text("Ótimo! Agora me diga como está se sentindo ou qual tipo de filme quer ver. 🎥")
        return RECOMMEND
    else:
        await update.message.reply_text("Por favor, digite **'Aceito'** para continuar ou use /start para recomeçar.")
        return TERMS

async def recommend_movie(update: Update, context: CallbackContext) -> None:
    user_text = update.message.text.lower()
    
    if any(word in user_text for word in ["triste", "feliz", "entediado", "animado"]):
        genero = "romance" if "triste" in user_text else "comédia" if "feliz" in user_text else "terror" if "entediado" in user_text else "ação"
        
        titulo, descricao, poster_url, movie_id = buscar_filme_por_genero(genero)
        
        if titulo:
            msg = f"🎬 *{titulo}*\n\n📖 {descricao}"
            if poster_url:
                await update.message.reply_photo(photo=poster_url, caption=msg, parse_mode='Markdown')
            else:
                await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text("Não encontrei um filme adequado. 😕")
    else:
        await update.message.reply_text("Me diga seu humor e um gênero de filme! Exemplo: 'Estou triste, quero um filme de romance'.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TERMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept_terms)],
            RECOMMEND: [MessageHandler(filters.TEXT & ~filters.COMMAND, recommend_movie)],
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    app.add_handler(conv_handler)
    
    print("🤖 Bot está rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
