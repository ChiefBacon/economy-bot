import discord
import configparser
import random
import psycopg2
from colorama import Fore
from datetime import datetime, timezone
import sys
import logging

fmt = '[%(levelname)s] %(asctime)s - %(message)s'
config = configparser.ConfigParser()

logging.basicConfig(format=fmt)

log = logging.getLogger('economy-bot')
log.setLevel(logging.DEBUG)

config.read('config/config.ini')

token = config['Discord']['token']
admin_id = config['Discord']['admin_id']

args = sys.argv

connection = psycopg2.connect(database=config["Database"]["name"], host=config["Database"]["host"], user=config["Database"]["user"], password=config["Database"]["password"], port=config.getint("Database", "port"))

crsr = connection.cursor()

crsr.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

crsr.execute('''CREATE TABLE IF NOT EXISTS Users(
    DiscordID TEXT PRIMARY KEY,
    Username TEXT,
    Balance FLOAT NOT NULL,
    IsAdmin BOOL DEFAULT FALSE
);''')

crsr.execute('''CREATE TABLE IF NOT EXISTS Transactions(
    Time TIMESTAMPTZ PRIMARY KEY DEFAULT NOW(),
    FromDiscordID TEXT,
    ToDiscordID TEXT,
    Amount FLOAT NOT NULL,
    Note TEXT
);''')

crsr.execute('''CREATE TABLE IF NOT EXISTS Items(
    item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ItemName TEXT UNIQUE NOT NULL,
    Price FLOAT NOT NULL,
    FilePath TEXT NOT NULL
);''')

# TODO: Load items from database instead
items = ["cat", "camera", "drone", "bed", "gamething"]
prices = [500, 500, 300, 500, 100]
files = ['/home/pi/economyBot/images/cat.png', '/home/pi/economyBot/images/camera.png', '/home/pi/economyBot/images/drone.png', '/home/pi/economyBot/images/bed.png', '/home/pi/economyBot/images/gamething.png']

yesorno = [True, False]

dice = [1, 2, 3, 4, 5, 6]

# Define Arcade Embed
arcadeEmbed = discord.Embed(title="Arcade", description="Welcome to the arcade!", color=0xffcc00)
arcadeEmbed.add_field(name="Guess The Number", value="Guess a number between 0 and 50. If you guess it, you win 100:coin:\nCost: 10:coin:\nCommand: /guess 24", inline=False)
arcadeEmbed.add_field(name="Dice Roll", value="Roll a die. If you roll a 5 you win 50:coin:\nCost: 10:coin:\nCommand: /roll", inline=False)

# Define Help Embed
helpEmbed = discord.Embed(title="Economy Bot", color=0xffcc00)
helpEmbed.add_field(name="Commands", value="?send - Send money to someone. Example: ?send 50\n?bal - Sends your current balance\n?arcade - See a list of games you can play\n?allbals - See the balance of everyone\n?worth - See the worth of everyone combined", inline=False)

# Define About Embed
aboutEmbed = discord.Embed(title="Economy Bot", description="Simple economy bot designed for me and my friends.", color=0xffcc00)
aboutEmbed.add_field(name="Creator", value="https://github.com/chiefbacon", inline=False)

# Define Shop Embed
shopEmbed = discord.Embed(title="The Shop", color=0xffcc00)
shopEmbed.add_field(name="Items", value="Cat - 500:coin:\nCamera - 500:coin:\nDrone - 300:coin:\nGame Thing - 100:coin:\nBed - 500:coin:\nSuper Pack - 1500:coin:\nCool Role - 500:coin:", inline=False)
shopEmbed.add_field(name="How To Buy", value="To buy something send /buy and then the name of the item you want to buy.", inline=False)


def commit_changes():
    # save db changes
    connection.commit()
    log.info('[✓] Backup Successful')


def get_user_data(discord_id):
    # Will return list in form [discord id, username, balance] if the user exists and None if the user doesn't
    crsr.execute('SELECT * FROM users WHERE DiscordID=%s;', [str(discord_id)])
    return crsr.fetchone()


def set_user_money(discord_id, new_balance: float):
    crsr.execute('UPDATE Users SET Balance = %s WHERE DiscordID=%s;', [new_balance, str(discord_id)])


def add_money_to_all(amount_to_add: float):
    crsr.execute('UPDATE Users SET Balance = Balance + %s;', [amount_to_add])


def update_user_password(discord_id, password):
    crsr.execute('UPDATE Users SET password=%s WHERE DiscordID=%s;', [password, str(discord_id)])


def user_exists(discord_id):
    crsr.execute('SELECT EXISTS(SELECT 1 FROM Users WHERE DiscordID=%s);', [str(discord_id)])
    return bool(crsr.fetchone()[0])


def add_user(discord_id, discord_username: str, default_balance: float):
    discord_id = str(discord_id)
    if not user_exists(discord_id):
        crsr.execute('INSERT INTO Users VALUES (%s, %s, %s);', [discord_id, discord_username, default_balance])


def log_transaction(discord_id_from, discord_id_to, amount: float, note: str):
    crsr.execute("INSERT INTO Transactions VALUES (%s, %s, %s, %s, %s);", [datetime.now(timezone.utc), str(discord_id_from), str(discord_id_to), amount, note])


def get_item_data(item_name: str):
    crsr.execute('SELECT * FROM Items WHERE ItemName=%s;', [item_name])
    return crsr.fetchone()


def transfer_money(userdata, recipient_data, amount_to_send):
    if userdata[2] >= amount_to_send:
        set_user_money(userdata[0], userdata[2] - amount_to_send)
        set_user_money(recipient_data[0], recipient_data[2] + amount_to_send)
        log_transaction(userdata[0], recipient_data[0], amount_to_send, "User Coin Transfer")
        commit_changes()
        return True
    else:
        return False


client = discord.Bot(activity=discord.Activity(type=discord.ActivityType.listening, name="/help"))


@client.event
async def on_ready():
    log.info(f'[✓] Bot connected to discord as {client.user.name}')


# @client.command(description="Get help with the bot")
# async def help(ctx):
    # await ctx.respond(embed=helpEmbed, ephemeral=True)


@client.command(description="Get info about the bot")
async def about(ctx):
    await ctx.respond(embed=aboutEmbed, ephemeral=True)


@client.command(description="See available arcade games")
async def arcade(ctx):
    await ctx.respond(embed=arcadeEmbed, ephemeral=True)


@client.command(description="Play the dice roll game")
async def roll(ctx):
    userdata = get_user_data(str(ctx.author.id))
    if userdata is not None:
        if userdata[2] >= 10:
            set_user_money(userdata[0], (userdata[2] - 10))
            log_transaction(userdata[0], 'system', 10, "Dice Roll Game Purchase")
            commit_changes()
            dice_roll = random.choice(dice)
            if dice_roll == 5:
                set_user_money(userdata[0], (userdata[2] + 50))
                log_transaction('system', userdata[0], 50, "Dice Roll Game Reward")
                await ctx.respond(':tada: You Won!')
                commit_changes()
            else:
                await ctx.respond(':neutral_face: You lost!')
        else:
            await ctx.respond(':negative_squared_cross_mark: You do not have enough money!', ephemeral=True)


@client.command(description="Backup the server's data")
async def backupdb(ctx):
    commit_changes()
    await ctx.respond(":white_check_mark: Backup Successful!", ephemeral=True)


@client.command(description="See items available in the shop")
async def shop(ctx):
    await ctx.respond(embed=shopEmbed, ephemeral=True)


@client.command(description="Buy something from the shop")
async def buy(ctx, item: discord.Option(str)):
    user = await client.fetch_user(ctx.author.id)
    userdata = get_user_data(str(ctx.author.id))
    if item.lower() in items:
        item_id = items.index(item.lower())
        if userdata is not None:
            if userdata[2] >= prices[item_id]:
                set_user_money(ctx.author.id, userdata[2] - prices[item_id])
                set_user_money(admin_id, get_user_data(admin_id)[2] + prices[item_id])
                log_transaction(userdata[0], admin_id, prices[item_id], f"Shop Purchase of {item}")
                commit_changes()
                await ctx.respond(":white_check_mark: Purchase Successful! Check your DMs")
                msg_to_delete = await user.send('Loading...')
                await user.send(file=discord.File(files[item_id]))
                await msg_to_delete.delete()
                log.info(f"[-] {ctx.author.name} purchased {items[item_id]}")
            else:
                await ctx.respond(':negative_squared_cross_mark: You do not have enough money!', ephemeral=True)
    elif item.lower() == "coolrole":
        if userdata is not None:
            if userdata[2] >= 500:
                set_user_money(ctx.author.id, userdata[2] - 500)
                set_user_money(admin_id, get_user_data(admin_id)[2] + 500)
                log_transaction(userdata[0], admin_id, 500, "Shop Purchase of Cool Role (this person is crazy)")
                commit_changes()
                await ctx.respond(':white_check_mark: Purchase Successful! Enjoy your role!')
                member = ctx.author
                role = get(member.guild.roles, name="I waste coins")
                await member.add_roles(role)
                log.info(f"[-] {ctx.author.name} purchased cool role (who would do that?){Fore.RESET}")
            else:
                await ctx.respond(':negative_squared_cross_mark: You do not have enough money!', ephemeral=True)


@client.command(description="See your current balance")
async def bal(ctx):
    userdata = get_user_data(str(ctx.author.id))
    log.debug(userdata)
    if userdata is not None:
        await ctx.respond((f'You have {str(userdata[2])}:coin:'), ephemeral=True)


@client.command(description="Set your web login password")
async def set_login(ctx, password: discord.Option(str)):
    update_user_password(ctx.author.id, password)
    await ctx.respond(':white_check_mark: Password Set!', ephemeral=True)


@client.command(description="Add coins to a user")
async def add(ctx, amount: discord.Option(float)):
    amount_to_add = amount
    userdata = get_user_data(str(ctx.author.id))
    if userdata[3]:
        set_user_money(userdata[0], userdata[2] + amount_to_add)
        log_transaction('system', userdata[0], amount_to_add, "Adding of coins to circulation")
        commit_changes()
        await ctx.respond((f':white_check_mark: Added {str(round(amount_to_add, 2))} :coin:'
                           f'Current Balance: {str(round(userdata[2], 2))}:coin:'), ephemeral=True)
        log.info(f"[+] Added {amount_to_add} to {ctx.author.name}")
    else:
        await ctx.respond(":negative_squared_cross_mark: You do not have permission to use this command!", ephemeral=True)
        log.warning(f'{ctx.author.name} tried to add money')


@client.command(description="Invest in the S T O N K S")
async def invest(ctx, amount: discord.Option(float)):
    invest_amount = amount
    userdata = get_user_data(str(ctx.author.id))
    if userdata is not None:
        if userdata[2] >= invest_amount:
            set_user_money(ctx.author.id, userdata[2] - invest_amount)
            log_transaction(userdata[0], 0, invest_amount, "Investment purchase")
            if random.choice(yesorno):
                await ctx.respond(':chart_with_upwards_trend: The stonks have gone up!')
                set_user_money(ctx.author.id, (userdata[2] + (invest_amount * 4)))
                log.info(f'[+] {ctx.author.name} invested {str(invest_amount)} and got a return of {str(invest_amount * 4)}')
                log_transaction(0, userdata[0], invest_amount * 4, "Investment return")
                commit_changes()
            else:
                await ctx.respond(':chart_with_downwards_trend: The stonks have gone down!')
                set_user_money(ctx.author.id, (userdata[2] + (invest_amount / 4)))
                log_transaction(0, userdata[0], invest_amount / 4, "Investment return")
                log.info(f'[-] {ctx.author.name} invested {str(invest_amount)} and got a return of {str(invest_amount / 4)}')
                commit_changes()
        else:
            await ctx.respond(':negative_squared_cross_mark: You do not have enough money!', ephemeral=True)


@client.command(description="See the balance of all users")
async def allbals(ctx):
    crsr.execute("SELECT * FROM Users;")
    userdatas = crsr.fetchall()
    balances_embed = discord.Embed(title="Economy Bot", color=0xffcc00)
    for user in userdatas:
        balances_embed.add_field(name=user[1], value=str(user[2]), inline=False)
    await ctx.respond(embed=balances_embed)


@client.command(description="Stop The Bot")
async def stop(ctx):
    userdata = get_user_data(str(ctx.author.id))
    if userdata[3]:
        await client.change_presence(status=discord.Status.idle)
        await ctx.respond(':white_check_mark: Stopping bot')
        quit()
    else:
        await ctx.respond(":negative_squared_cross_mark: You do not have permission to use this command!")
        log.warning(f'[!] {ctx.author.name} tried to stop bot')


@client.command(description="See the total worth of the server")
async def worth(ctx):
    crsr.execute("SELECT SUM(Balance) as sum_balance FROM Users;")
    total = crsr.fetchone()[0]
    total_embed = discord.Embed(color=0xffcc00)
    total_embed.add_field(name="Total Worth", value=f"{str(total)}:coin:", inline=False)
    await ctx.respond(embed=total_embed)


@client.command(description="Mark the bot as offline")
async def offline(ctx):
    userdata = get_user_data(str(ctx.author.id))
    if userdata[3]:
        await client.change_presence(status=discord.Status.offline)
        await ctx.respond(':white_check_mark: Changing status to offline', ephemeral=True)
        log.warning('[✓] Changing to offline')
    else:
        await ctx.respond(":negative_squared_cross_mark: You do not have permission to use this command!", ephemeral=True)
        log.warning(f'[!] {ctx.author.name} tried to offline bot')


@client.command(description="Add a new user to the bot")
async def adduser(ctx, user: discord.Option(discord.Member)):
    user_to_add = user.id
    userdata = get_user_data(user_to_add)
    if userdata is None:
        add_user(user_to_add, str(user), 50)
        log_transaction(ctx.author.id, 0, 50, f"New User {str(user)} added to system")
        await ctx.respond(f':white_check_mark: Success! Added User <@!{str(user_to_add)}>', ephemeral=True)
        log.info(f'[✓] User {str(user_to_add)} Added')
        commit_changes()
    else:
        await ctx.respond(f':negative_squared_cross_mark: Error! User <@!{str(user_to_add)}> already exists!', ephemeral=True)
        log.warning(f'[!] Tried to add user {str(user_to_add)} but user already existed')


@client.command(description="Guess a number between 0 and 50")
async def guess(ctx, number: discord.Option(int)):
    number_guessed = number
    if number_guessed > 50 or number_guessed < 0:
        await ctx.respond(':grey_question: The number must be between 0 and 50.', ephemeral=True)
    else:
        random_number = random.randrange(51)
        userdata = get_user_data(str(ctx.author.id))
        if userdata is not None:
            if userdata[2] >= 10:
                set_user_money(ctx.author.id, userdata[2] - 10)
                log_transaction(userdata[0], 'system', 10, "Number guess purchase")
                commit_changes()
                if random_number == int(number_guessed):
                    set_user_money(ctx.author.id, userdata[2] + 50)
                    log_transaction('system', userdata[0], 50, "Number guess reward")
                    await ctx.respond(':tada: You Won!')
                    commit_changes()
                else:
                    await ctx.respond(':neutral_face: You lost!')
            else:
                await ctx.respond(':negative_squared_cross_mark: You do not have enough money!', ephemeral=True)


@client.command(description="Add money to all users")
async def addall(ctx, amount: discord.Option(float)):
    userdata = get_user_data(str(ctx.author.id))
    if userdata[3]:
        add_all_amount = float(amount)
        add_money_to_all(add_all_amount)
        await ctx.respond(f':white_check_mark: Success! Added {str(add_all_amount)}:coin: to all users', ephemeral=True)
        log.info(f'[+] Added {str(add_all_amount)} to all users')
        commit_changes()
    else:
        await ctx.respond(":negative_squared_cross_mark: You do not have permission to use this command!", ephemeral=True)
        log.warning(f'[!] {ctx.author.name} tried to add money to all')


@client.command(description="Send coins to another user")
async def send(ctx, amount: discord.Option(float), user: discord.Option(discord.Member)):
    amount_to_send = amount
    id_to_send_to = str(user.id)
    userdata = get_user_data(str(ctx.author.id))
    recipient_data = get_user_data(id_to_send_to)

    can_send_negative = userdata[3]

    if userdata is not None and recipient_data is not None:
        if amount_to_send < 0 and can_send_negative:
            transfer = transfer_money(userdata, recipient_data, amount_to_send)
            if transfer:
                await ctx.respond(f':white_check_mark: Sent {str(amount_to_send)}:coin: to <@!{str(id_to_send_to)}>')
                log.info(f'[+] User {ctx.author.name} sent {str(amount_to_send)} to {str(id_to_send_to)}')
            else:
                await ctx.respond(':negative_squared_cross_mark: You do not have enough!', ephemeral=True)
        elif amount_to_send < 0:
            await ctx.respond(':negative_squared_cross_mark: That is a negative number!', ephemeral=True)
            log.warning(f'[!] User {ctx.author.name} tried to send negative money')
        else:
            transfer = transfer_money(userdata, recipient_data, amount_to_send)
            if transfer:
                await ctx.respond(':white_check_mark: Sent {str(amount_to_send)}:coin: to <@!{str(id_to_send_to)}>')
                log.info(f'[+] User {ctx.author.name} sent {str(amount_to_send)} to {str(id_to_send_to)}')
            else:
                await ctx.respond(':negative_squared_cross_mark: You do not have enough!', ephemeral=True)

client.run(token)
