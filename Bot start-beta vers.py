import nextcord
from nextcord.ext import commands
import asyncio

TOKEN = '=token'  # Замените на Ваш реальный токен

intents = nextcord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

MUTE_ROLE_NAME = "Muted"

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    for guild in bot.guilds:
        mute_role = nextcord.utils.get(guild.roles, name=MUTE_ROLE_NAME)
        if mute_role is None:
            mute_role = await guild.create_role(name=MUTE_ROLE_NAME)
            print(f'Создана роль: {mute_role.name} в гильдии: {guild.name}')
        else:
            print(f'Роль {mute_role.name} уже существует в гильдии: {guild.name}')

    try:
        with open('icon.png', 'rb') as avatar_file:
            avatar_data = avatar_file.read()
    except FileNotFoundError:
        avatar_data = None

    for guild in bot.guilds:
        for channel in guild.channels:
            if isinstance(channel, nextcord.TextChannel):
                # Получаем список вебхуков в канале
                webhooks = await channel.webhooks()
                # Проверяем, существует ли вебхук с именем бота
                if any(wh.name == bot.user.name for wh in webhooks):
                    print(f'Вебхук с именем {bot.user.name} уже существует в {channel.name}s.')
                    continue  # Переходим к следующему каналу

                try:
                    webhook = await channel.create_webhook(name=bot.user.name, avatar=avatar_data)
                    print(f'Webhook создан в {channel.name}: {webhook.url}')
                except nextcord.Forbidden:
                    print(f'Нет прав для создания вебхука в {channel.name}.')
                except nextcord.HTTPException as e:
                    print(f'Ошибка при создании вебхука в {channel.name}: {e}')

@bot.slash_command(name="helpme", description="Выводит инструкции по использованию бота.")
async def helpme(interaction: nextcord.Interaction):
    instructions = (
        "Добро пожаловать! Вот что Вы можете сделать с этим ботом:\n"
        "1. Используйте `/ping`, чтобы получить ответ 'Pong!'.\n"
        "2. Используйте `/kick @пользователь <время>`, чтобы кикнуть пользователя на указанное время.\n"
        "3. Используйте `/ban @пользователь <время>`, чтобы забанить пользователя на указанное время.\n"
        "4. Используйте `/mute @пользователь <время>`, чтобы замьютить пользователя.\n"
        "5. Используйте `/unmute @пользователь`, чтобы анмьютить пользователя.\n"
        "6. Используйте `/unban @пользователь`, чтобы разбанить пользователя.\n"
        "Вся Информация"
    )
    await interaction.send(instructions)

@bot.slash_command(name="ping", description="Проверка работы бота.")
async def ping(interaction: nextcord.Interaction):
    await interaction.send("Bot Full Working")

@bot.slash_command(name="kick", description="Кикнуть пользователя на заданное время.")
@commands.has_role('admins')
async def kick(interaction: nextcord.Interaction, member: nextcord.Member, duration: int):
    await member.kick(reason=f"Kicked by {interaction.user.name} for {duration} seconds.")
    await interaction.send(f"{member.name} был кикнут на {duration} секунд.")

    await asyncio.sleep(duration)

    await interaction.guild.unban(member)
    await interaction.channel.send(f"{member.name} возвращается обратно после кика.")

@kick.error
async def kick_error(interaction: nextcord.Interaction, error):
    if isinstance(error, commands.MissingPermissions):
        await interaction.send("У вас нет прав для использования этой команды.")
    else:
        await interaction.send("Произошла ошибка. Пожалуйста, попробуйте снова.")

@bot.slash_command(name="ban", description="Забанить пользователя на заданное время.")
@commands.has_permissions(administrator=True)
async def ban(interaction: nextcord.Interaction, member: nextcord.Member, duration: int):
    await member.ban(reason=f"Banned by {interaction.user.name} for {duration} seconds.")
    await interaction.send(f"{member.name} был забанен на {duration} секунд.")

    await asyncio.sleep(duration)

    # Разбаниваем пользователя
    await interaction.guild.unban(member)
    await interaction.channel.send(f"{member.name} был разбанен после {duration} секунд.")

@ban.error
async def ban_error(interaction: nextcord.Interaction, error):
    if isinstance(error, commands.MissingPermissions):
        await interaction.send("У вас нет прав для использования этой команды.")
    else:
        await interaction.send("Произошла ошибка. Пожалуйста, попробуйте снова.")


@bot.slash_command(name="mute", description="Замьютить пользователя на заданное время.")
@commands.has_permissions(administrator=True)
async def mute(interaction: nextcord.Interaction, member: nextcord.Member, duration: int):
    mute_role = nextcord.utils.get(interaction.guild.roles, name=MUTE_ROLE_NAME)

    if mute_role is None:
        await interaction.send(f"Роль '{MUTE_ROLE_NAME}' не найдена. Пожалуйста, создайте её.")
        return

    if interaction.guild.me.top_role <= mute_role:
        await interaction.send(
            "У меня нет прав для назначения роли 'Muted'. Убедитесь, что моя роль выше роли 'Muted'.")
        return

    await member.add_roles(mute_role)
    await interaction.send(f"{member.name} был замьючен на {duration} секунд.")

    await asyncio.sleep(duration)

    await member.remove_roles(mute_role)
    await interaction.channel.send(f"{member.name} был размьючен после {duration} секунд.")


@mute.error
async def mute_error(interaction: nextcord.Interaction, error):
    if isinstance(error, commands.MissingPermissions):
        await interaction.send("У вас нет прав для использования этой команды.")
    else:
        await interaction.send("Произошла ошибка. Пожалуйста, попробуйте снова.")


@bot.slash_command(name="unmute", description="Анмьютить пользователя.")
@commands.has_permissions(administrator=True)
async def unmute(interaction: nextcord.Interaction, member: nextcord.Member):
    mute_role = nextcord.utils.get(interaction.guild.roles, name=MUTE_ROLE_NAME)

    if mute_role is None:
        await interaction.send(f"Роль '{MUTE_ROLE_NAME}' не найдена. Пожалуйста, создайте её.")
        return

    if mute_role not in member.roles:
        await interaction.send(f"{member.name} не имеет роли '{MUTE_ROLE_NAME}'.")
        return

    if interaction.guild.me.top_role <= mute_role:
        await interaction.send("У меня нет прав для снятия роли 'Muted'. Убедитесь, что моя роль выше роли 'Muted'.")
        return

    await member.remove_roles(mute_role)
    await interaction.send(f"{member.name} был размьючен.")


@unmute.error
async def unmute_error(interaction: nextcord.Interaction, error):
    if isinstance(error, commands.MissingPermissions):
        await interaction.send("У вас нет прав для использования этой команды.")
    else:
        await interaction.send("Произошла ошибка. Пожалуйста, попробуйте снова.")

@bot.slash_command(name="unban", description="Разбанить пользователя.")
@commands.has_permissions(administrator=True)
async def unban(interaction: nextcord.Interaction, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        # Проверяем, если пользователь забанен
        banned_users = await interaction.guild.bans()
        if user not in [ban_entry.user for ban_entry in banned_users]:
            await interaction.send(f"Пользователь с ID {user_id} не забанен.")
            return

        await interaction.guild.unban(user)
        await interaction.send(f"{user.name} был разбанен.")
    except nextcord.NotFound:
        await interaction.send(f"Пользователь с ID {user_id} не найден.")
    except nextcord.Forbidden:
        await interaction.send("У меня нет прав, чтобы разбанить этого пользователя.")
    except nextcord.HTTPException:
        await interaction.send("Произошла ошибка при разбанивании пользователя.")
    except Exception as e:
        await interaction.send(f"Произошла непредвиденная ошибка: {str(e)}")

@unban.error
async def unban_error(interaction: nextcord.Interaction, error):
    if isinstance(error, commands.MissingPermissions):
        await interaction.send("У вас нет прав для использования этой команды.")
    else:
        await interaction.send("Произошла ошибка. Пожалуйста, попробуйте снова.")

# Запускаем бота
bot.run(TOKEN)
