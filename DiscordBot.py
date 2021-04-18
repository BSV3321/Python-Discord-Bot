import discord
import os
import random
import json
import datetime
import re
from discord.ext import commands, tasks
from random import choice
from discord.utils import get
from discord.ext.commands import cooldown, BucketType
from urllib import parse, request

os.chdir("E:\\VSCode\\Python\\02 - DiscordBot\\DCB2")

bot = commands.Bot(command_prefix='$')


mainshop = [{"name":"Watch","price":1000}]

status = ['$help', 'Go and buy something']
queue = []

#tasks
@tasks.loop(seconds=30)
async def change_status():
    await bot.change_presence(activity=discord.Game(choice(status)))

#event
@bot.event
async def on_ready():
    change_status.start()
    print('bot is ready!!!')

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='general')
    await channel.send(f'Welcome {member.mention}!  Ready to jam out? See `?help` command for details!')

#commands
@bot.command(help="To buy item's from shop")
async def buy(ctx, item, amount=1):
    await open_account(ctx.author)

    res = await buy_this(ctx.author, item, amount)

    if not res[0]:
        if res[1]==1:
            await ctx.send("That object isn't there!")
            return
        if res[1]==2:
            await ctx.send(f"You don't have enough money in your wallet to buy {amount} {item}")
            return
    
    await ctx.send(f"You just bought {amount} {item}")

@bot.command(help='To check your inventory')
async def inv(ctx):
    await open_account(ctx.author)
    user = ctx.author
    users = await get_bank_data()

    try:
        bag = users[str(user.id)]["bag"]
    except:
        bag = []

    embed=discord.Embed(title="Inventory", color=0x0062ff)
    for item in bag:
        name = item["item"]
        amount = item["amount"]

        embed.add_field(name=name, value=amount)

    await ctx.send(embed=embed)

async def buy_this(user, item_name, amount):
    item_name = item_name.lower()
    name_ = None
    for item in mainshop:
        name = item["name"].lower()
        if name == item_name:
            name_ = name
            price = item["price"]
            break

    if name_ == None:
        return [False, 1]

    cost = price*amount

    users = await get_bank_data()

    bal = await update_bank(user)

    if bal[0]<cost:
        return [False, 2]

    try:
        index = 0
        t = None
        for thing in users[str(user.id)]["bag"]:
            n = thing["item"]
            if n == item_name:
                old_amt = thing["amount"]
                new_amt = old_amt + amount
                users[str(user.id)]["bag"][index]["amount"] = new_amt
                t = 1
                break
            index+=1
        if t == None:
            obj = {"item":item_name, "amount":amount}
            users[str(user.id)]["bag"].append(obj)
    except:
        obj = {"item":item_name, "amount":amount}
        users[str(user.id)]["bag"] = [obj]

    with open("mainbank.json", "w") as f:
        json.dump(users, f)

    await update_bank(user, cost*-1, "wallet")

    return[True, "Worked"]


@bot.command(help='To check item in shop')
async def shop(ctx):
    embed=discord.Embed(title="SHOP", color=0x0062ff)

    for item in mainshop:
        name = item["name"]
        price = item["price"]
        embed.add_field(name=name, value=f"{price}")


    await ctx.send(embed=embed)

@bot.command(name='dice')
async def dice(ctx):
    responses = ['1', '2', '3', '4', '5', '6']
    await ctx.send(choice(responses))

@bot.command(help='To check your balance')
async def balance(ctx):
    await open_account(ctx.author)
    user = ctx.author
    users = await get_bank_data()

    wallet_amt = users[str(user.id)]["wallet"]
    bank_amt = users[str(user.id)]["bank"]

    embed=discord.Embed(title=f"{ctx.author.name}'s balance", color=0x0062ff)
    embed.add_field(name="Wallet balance", value=wallet_amt)
    embed.add_field(name="bank balance", value=bank_amt)
    await ctx.send(embed=embed)

@bot.command( help='Work and get some money')
async def work(ctx):
    await ctx.send("Working as")

    job = ['pizza delivery', 'electrical worker', 'trucker', 'bus driver', 'taxi driver']
    await ctx.send(choice(job))

    users = await get_bank_data()

    user = ctx.author

    earnings = random.randrange(500)

    wallet_amt = users[str(user.id)]["wallet"]

    await open_account(ctx.author)
    user = ctx.author
    users = await get_bank_data()

    embed=discord.Embed(title=f"{ctx.author.name}'s salary", color=0x0062ff)
    embed.add_field(name="Your salary", value=earnings)
    embed.add_field(name="In your wallet", value=wallet_amt)
    await ctx.send(embed=embed)

    users[str(user.id)]["wallet"] += earnings

    with open("mainbank.json", "w") as f:
        json.dump(users,f)

async def open_account(user):

    users = await get_bank_data()

    if str(user.id) in users:
        return False
    else:
        users[str(user.id)] = {}
        users[str(user.id)]["wallet"] = 0
        users[str(user.id)]["bank"] = 0


    with open("mainbank.json", "w") as f:
        json.dump(users,f)
    return True

@bot.command(help='To withdraw your money from bank')
async def withdraw(ctx, amount=None):
    await open_account(ctx.author)

    if amount == None:
        await ctx.send("Enter your amount")
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)
    if amount>bal[1]:
        await ctx.send("Invalid amount")
        return
    if amount<0:
        await ctx.send("Invalid amount")
        return

    await update_bank(ctx.author, amount)
    await update_bank(ctx.author, -1*amount, "bank")

    await open_account(ctx.author)
    user = ctx.author
    users = await get_bank_data()

    wallet_amt = users[str(user.id)]["wallet"]
    bank_amt = users[str(user.id)]["bank"]

    embed=discord.Embed(title=f"{ctx.author.name}'s bank balance", color=0x0062ff)
    embed.add_field(name="Withdrew", value=amount)
    embed.add_field(name="Wallet balance", value=wallet_amt)
    embed.add_field(name="Bank balance", value=bank_amt)
    await ctx.send(embed=embed)


@bot.command(help='To deposit your money in bank')
async def deposit(ctx, amount=None):
    await open_account(ctx.author)

    if amount == None:
        await ctx.send("Enter your amount")
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)
    if amount>bal[0]:
        await ctx.send("Invalid amount")
        return
    if amount<0:
        await ctx.send("Invalid amount")
        return
 
    await update_bank(ctx.author, -1*amount)
    await update_bank(ctx.author, amount, "bank")

    await open_account(ctx.author)
    user = ctx.author
    users = await get_bank_data()

    wallet_amt = users[str(user.id)]["wallet"]
    bank_amt = users[str(user.id)]["bank"]

    embed=discord.Embed(title=f"{ctx.author.name}'s bank balance", color=0x0062ff)
    embed.add_field(name="Wallet balance", value=wallet_amt)
    embed.add_field(name="Deposited", value=amount)
    embed.add_field(name="Bank balance", value=bank_amt)
    await ctx.send(embed=embed)

@bot.command(help='To send money')
async def send(ctx, member:discord.Member, amount=None):
    await open_account(ctx.author)
    await open_account(member)

    if amount == None:
        await ctx.send("Enter your amount")
        return

    bal = await update_bank(ctx.author)
    if amount == "all":
        amount = bal[0]

    amount = int(amount)
    if amount>bal[1]:
        await ctx.send("Invalid amount")
        return
    if amount<0:
        await ctx.send("Invalid amount")
        return

    await update_bank(ctx.author, -1*amount, "bank")
    await update_bank(member, amount, "bank")

    await ctx.send(f"you gave {amount} of your money")

    await open_account(ctx.author)
    user = ctx.author
    users = await get_bank_data()

    wallet_amt = users[str(user.id)]["wallet"]
    bank_amt = users[str(user.id)]["bank"]

    embed=discord.Embed(title=f"{ctx.author.name}'s balance", color=0x0062ff)
    embed.add_field(name="Wallet balance", value=wallet_amt)
    embed.add_field(name="bank balance", value=bank_amt)
    await ctx.send(embed=embed)

@bot.command(help='Play and get some money difficulty : Easy X2')
async def qwerty1(ctx, amount=None):
    await open_account(ctx.author)

    if amount == None:
        await ctx.send("Enter your amount")
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)
    if amount>bal[0]:
        await ctx.send("Invalid amount")
        return
    if amount<0:
        await ctx.send("Invalid amount")
        return

    final =[]
    for i in range(6):
        a = random.choice(["Q", "W", "E", "R", "T", "Y"])

        final.append(a)

        await ctx.send(str(final))

    if final[0] == final[1] or final[0] == final[2] or final[0] == final[2] or final[2] == final[3]:
        await update_bank(ctx.author, 2*amount)
        await ctx.send("You Won!!!")
    else:
        await update_bank(ctx.author, -1*amount)
        await ctx.send("You Lose!!!")

    if final[0] == final[1] or final[0] == final[2] or final[0] == final[2] or final[2] == final[3]:
        await open_account(ctx.author)
        user = ctx.author
        users = await get_bank_data()

        wallet_amt = users[str(user.id)]["wallet"]

        embed=discord.Embed(title=f"Congratulation {ctx.author.name}", color=0x008000)
        embed.add_field(name="You got", value=2*amount)
        embed.add_field(name="Wallet balance", value=wallet_amt)
        await ctx.send(embed=embed)
    else:
        await open_account(ctx.author)
        user = ctx.author
        users = await get_bank_data()

        wallet_amt = users[str(user.id)]["wallet"]

        embed=discord.Embed(title=f"You lose try again next time {ctx.author.name}", color=0xff0000)
        embed.add_field(name="You lose", value=-1*amount)
        embed.add_field(name="Wallet balance", value=wallet_amt)
        await ctx.send(embed=embed)

@bot.command(help='Play and get some money difficulty : Medium X3')
async def qwerty2(ctx, amount=None):
    await open_account(ctx.author)

    if amount == None:
        await ctx.send("Enter your amount")
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)
    if amount>bal[0]:
        await ctx.send("Invalid amount")
        return
    if amount<0:
        await ctx.send("Invalid amount")
        return

    final =[]
    for i in range(6):
        a = random.choice(["Q", "W", "E", "R", "T", "Y"])

        final.append(a)

        await ctx.send(str(final))

    if final[0] == final[1] or final[0] == final[2] or final[2] == final[1]:
        await update_bank(ctx.author, 3*amount)
        await ctx.send("You Won!!!")
    else:
        await update_bank(ctx.author, -2*amount)
        await ctx.send("You Lose!!!")

    if final[0] == final[1] or final[0] == final[2] or final[2] == final[1]:
        await open_account(ctx.author)
        user = ctx.author
        users = await get_bank_data()

        wallet_amt = users[str(user.id)]["wallet"]

        embed=discord.Embed(title=f"Congratulation {ctx.author.name}", color=0x008000)
        embed.add_field(name="You got", value=3*amount)
        embed.add_field(name="Wallet balance", value=wallet_amt)
        await ctx.send(embed=embed)
    else:
        await open_account(ctx.author)
        user = ctx.author
        users = await get_bank_data()

        wallet_amt = users[str(user.id)]["wallet"]

        embed=discord.Embed(title=f"You lose try again next time {ctx.author.name}", color=0xff0000)
        embed.add_field(name="You lose", value=-1*amount)
        embed.add_field(name="Wallet balance", value=wallet_amt)
        await ctx.send(embed=embed)

@bot.command(help='Play and get some money difficulty : Hard X10')
async def qwerty3(ctx, amount=None):
    await open_account(ctx.author)

    if amount == None:
        await ctx.send("Enter your amount")
        return

    bal = await update_bank(ctx.author)

    amount = int(amount)
    if amount>bal[0]:
        await ctx.send("Invalid amount")
        return
    if amount<0:
        await ctx.send("Invalid amount")
        return

    final =[]
    for i in range(6):
        a = random.choice(["Q", "W", "E", "R", "T", "Y"])

        final.append(a)

        await ctx.send(str(final))

    if final[4] == final[2]:
        await update_bank(ctx.author, 10*amount)
        await ctx.send("You Won!!! JACKPOT!!!!!!!!!")
    else:
        await update_bank(ctx.author, -3*amount)
        await ctx.send("You Lose!!!")

    if  final[4] == final[2]:
        await open_account(ctx.author)
        user = ctx.author
        users = await get_bank_data()

        wallet_amt = users[str(user.id)]["wallet"]

        embed=discord.Embed(title=f"Congratulation {ctx.author.name}", color=0x008000)
        embed.add_field(name="You got", value=6*amount)
        embed.add_field(name="Wallet balance", value=wallet_amt)
        await ctx.send(embed=embed)
    else:
        await open_account(ctx.author)
        user = ctx.author
        users = await get_bank_data()

        wallet_amt = users[str(user.id)]["wallet"]

        embed=discord.Embed(title=f"You lose try again next time {ctx.author.name}", color=0xff0000)
        embed.add_field(name="You lose", value=-2*amount)
        embed.add_field(name="Wallet balance", value=wallet_amt)
        await ctx.send(embed=embed)

@bot.command(help='To rob someone')
async def rob(ctx, member:discord.Member):
    await open_account(ctx.author)
    await open_account(member)

    bal = await update_bank(member)

    if bal[0]<100:
        await ctx.send("You trying to rob and you found nothing")
        return
    earnings = random.randrange(0, bal[0])

    await update_bank(ctx.author, earnings)
    await update_bank(member, -1*earnings)

    await ctx.send(f"you robbed and got {earnings}")

async def get_bank_data():
    with open("mainbank.json", "r") as f:
        users = json.load(f)
    
    return users

async def update_bank(user, change=0, mode="wallet"):
    users=await get_bank_data()

    users[str(user.id)][mode] += change

    with open("mainbank.json", "w") as f:
        json.dump(users,f)
    
    bal = [users[str(user.id)]["wallet"], users[str(user.id)]["bank"]]
    return bal

bot.run('ODMyMTMyMjEwMTMxODYxNTI0.YHfVgw.zMNNVqjsTadkfAMZk6ccXTPHwf8')