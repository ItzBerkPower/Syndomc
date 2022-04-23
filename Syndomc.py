#Syndomc 1.0

#Imports
import discord
from discord.ext import commands
import json
import os
import random
import asyncio
import traceback
import sys
from discord.ext.commands import BucketType
from discord.ext.commands import CommandOnCooldown

#File Location
os.chdir("File Location Here")

#Prefix for bot
client = commands.Bot(command_prefix = "sn!")

#Shop
mainshop = [{"name":"Wheel","price":1450,"description": "Wheel of luck, spin the wheel to either win money, or lose money!"}]

#Job List
jobslist = [{"name": "Librarian", "description": "Sell books"}]


#Remove existing help command
client.remove_command("help")

#When bot is ready
@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="Under Construction!|sn!help"))
    print("Ready")

#Help command
@client.command()
async def help(ctx):

    em = discord.Embed(title = "Need Help?",color = discord.Color.purple())
    em.add_field(name = "Support Server",value = "https://discord.gg/7npR2MYZNc")
    em.add_field(name = "Current Commands",value = "sn!work - Work command \n sn!help - Help command \n sn!balance - Balance command \n sn!deposit - Deposit command \n sn!withdraw - Withdraw command")
    await ctx.send(embed = em)



#Cooldown
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        msg = "**Woah there, **your still on cooldown, try again in {:.2f}s".format(error.retry_after)
        await ctx.send(msg)



#Work command
@client.command()
@commands.cooldown(rate = 1, per = 20, type=BucketType.user)
async def work(ctx):
    await open_account(ctx.author)
    users = await get_bank_data()
    user = ctx.author

    earnings = random.randrange(101,200)
    message = random.randint(1,3)

    if message == 1:
        await ctx.send(f"**Nice work {ctx.author.name}!** \n You worked at an ice-cream truck for ${earnings}!")

    elif message == 2:
        await ctx.send(f"**Nice work {ctx.author.name}!** \n You fished for ${earnings}!")
    
    elif message == 3:
        await ctx.send(f"**Nice work {ctx.author.name}!** \n You begged on the street for ${earnings}!")

    users[str(user.id)]["wallet"] += earnings

    with open("mainbank.json","w") as f:
        json.dump(users,f)


# Wheel command
@client.command()
async def wheel(ctx):

    await open_account(ctx.author)
    users = await get_bank_data()
    user = ctx.author

    for i in users[str(user.id)]["bag"]:

        if "wheel" in list(i.values()):

            if i["amount"] > 0:

                amount = random.randrange(-1001,1001) #Amount to win or lose

                if amount < 0:
                    users[str(user.id)]["wallet"] += amount
                    amount = amount * -1
                    await ctx.send(f"**Sorry for your loss {ctx.author.name}**! \n You spun the wheel and lost ${amount} \n Better luck next time!")

                elif amount > 0:
                    users[str(user.id)]["wallet"] += amount
                    await ctx.send(f"**Boss work {ctx.author.name}**! \n You spun the wheel and got ${amount}!")
            
            else:
                await ctx.send("You need a wheel to spin a wheel!")


        else:
            await ctx.send("You need a wheel to spin a wheel!")


#Job List command
@client.command()
async def jobs(ctx):

    em = discord.Embed(title = "Jobs List")

    for item in jobslist:
        name = item["name"]
        desc = item["description"]
        em.add_field(name = name, value = f"{desc}")

    await ctx.send(embed = em)

#@client.command()
#async def work(ctx, name):




#Balance command
@client.command(aliases = ["bal"])
async def balance(ctx):

    await open_account(ctx.author)
    users = await get_bank_data()
    user = ctx.author

    wallet = users[str(user.id)]["wallet"]
    bank = users[str(user.id)]["bank"]

    em = discord.Embed(title = f"{ctx.author.name}'s balance",color = discord.Color.green())
    em.add_field(name = "Wallet",value = wallet)
    em.add_field(name = "Bank",value = bank)
    await ctx.send(embed = em)


@client.command(aliases = ["dep"])
async def deposit(ctx, amount = None):
    await open_account(ctx.author)

    if amount == None:
        await ctx.send("Please enter an amount")
        return

    bal = await update_bank(ctx.author)
    if amount == "all":
        amount = bal[0]

    amount = int(amount)

    if amount > bal[0]:
        await ctx.send("You do not have enough in your wallet!")
        return 

    if amount < 0:
        await ctx.send("The amount must be positive!")
        return 

    await update_bank(ctx.author,-1*amount)
    await update_bank(ctx.author,amount,"bank")

    await ctx.send(f"You deposited {amount}!")

@client.command(aliases=["with"])
async def withdraw(ctx,amount = None):
    await open_account(ctx.author)

    if amount == None:
        await ctx.send("You need an amount to withdraw!")
        return

    bal = await update_bank(ctx.author)
    amount = int(amount)
    
    if amount > bal[1]:
        await ctx.send("You don't have that much money to withdraw!")
        return

    await update_bank(ctx.author, amount)
    await update_bank(ctx.author, -1*amount, "bank")

    await ctx.send(f"You withdrew ${amount}!")

@client.command()
async def shop(ctx):
    em = discord.Embed(title = "Shop")

    for item in mainshop:
        name = item["name"]
        price = item["price"]
        desc = item["description"]
        em.add_field(name = name, value = f"${price} | {desc}")

    await ctx.send(embed = em)

@client.command()
async def bag(ctx):
    await open_account(ctx.author)
    user = ctx.author
    users = await get_bank_data()

    try:
        bag = users[str(user.id)]["bag"]

    except:
        bag = []

    em = discord.Embed(title = "Bag")

    for item in bag:
        if item["amount"] > 0:
            name = item["item"]
            amount = item["amount"]
            em.add_field(name = name, value = amount)    

    await ctx.send(embed = em)    


@client.command()
async def buy(ctx,item,amount = 1):
    await open_account(ctx.author)

    res = await buy_this(ctx.author,item,amount)

    if not res[0]:
        if res[1]==1:
            await ctx.send("That object isn't there!")
            return

        elif res[1]==2:
            await ctx.send(f"You don't have enough money in your wallet to buy {amount}!")
            return

    await ctx.send(f"You just bought {amount} {item}!")

async def buy_this(user,item_name,amount):
    item_name = item_name.lower()
    name_ = None

    for item in mainshop:
        name = item["name"].lower()

        if name == item_name:
            name_ = name
            price = item["price"]
            break

    if name_ == None:
        return [False,1]

    cost = price*amount

    users = await get_bank_data()

    bal = await update_bank(user)

    if bal[0]<cost:
        return [False,2]


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
            obj = {"item":item_name , "amount" : amount}
            users[str(user.id)]["bag"].append(obj)
    except:
        obj = {"item":item_name , "amount" : amount}
        users[str(user.id)]["bag"] = [obj]        

    with open("mainbank.json","w") as f:
        json.dump(users,f)

    await update_bank(user,cost*-1,"wallet")

    return [True,"Worked"]

@client.command()
async def sell(ctx,item,amount = 1):
    await open_account(ctx.author)

    res = await sell_this(ctx.author,item,amount)

    if not res[0]:
        if res[1]==1:
            await ctx.send("That Object isn't there!")
            return
        if res[1]==2:
            await ctx.send(f"You don't have {amount} {item} in your bag.")
            return
        if res[1]==3:
            await ctx.send(f"You don't have {item} in your bag.")
            return

    await ctx.send(f"You just sold {amount} {item}.")

async def sell_this(user,item_name,amount,price = None):
    item_name = item_name.lower()
    name_ = None
    for item in mainshop:
        name = item["name"].lower()
        if name == item_name:
            name_ = name
            if price==None:
                price = 0.9* item["price"]
            break

    if name_ == None:
        return [False,1]

    cost = price*amount

    users = await get_bank_data()

    bal = await update_bank(user)


    try:
        index = 0
        t = None
        for thing in users[str(user.id)]["bag"]:
            n = thing["item"]
            if n == item_name:
                old_amt = thing["amount"]
                new_amt = old_amt - amount
                if new_amt < 0:
                    return [False,2]
                users[str(user.id)]["bag"][index]["amount"] = new_amt
                t = 1
                break
            index+=1 
        if t == None:
            return [False,3]
    except:
        return [False,3]    

    with open("mainbank.json","w") as f:
        json.dump(users,f)

    await update_bank(user,cost,"wallet")

    return [True,"Worked"]

    





#Open the account for the user
async def open_account(user):

    users = await get_bank_data()

    if str(user.id) in users:
        return False

    else:
        users[str(user.id)] = {}
        users[str(user.id)]["wallet"] = 0 
        users[str(user.id)]["bank"] = 0

    with open("mainbank.json","w") as f:
        json.dump(users,f)
    return True



#Get bank data from the user
async def get_bank_data():
    with open("mainbank.json","r") as f:
        users = json.load(f)

    return users


#Update bank details from user
async def update_bank(user,change = 0,mode = "wallet"):
    users = await get_bank_data()

    users[str(user.id)][mode] += change 

    with open("mainbank.json","w") as f:
        json.dump(users,f)

    bal = [users[str(user.id)]["wallet"],users[str(user.id)]["bank"]]
    return bal



#Bot ID
client.run("Client Code here")