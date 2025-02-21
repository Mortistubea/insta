from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()


BOT_TOKEN = env.str("BOT_TOKEN")  # Bot token
ADMINS = [int(x) for x in env.list("ADMINS")]  # Adminlar ro'yxati