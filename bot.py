import discord
import requests
import json
from matplotlib import pyplot as plt

TOKEN = 'MTA4NjEyNzEyMTkyNTE0NDcwNg.GW3ivr.274BILb-kMBYmAubZcqpqyuaj4BVqsxv7yVpvc'

client = discord.Client(intents=discord.Intents.all())

# json
url = "https://script.google.com/macros/s/AKfycbyY3Bol7wFrcyFCk-FIf6oUMn731RkZAglYZd2WoTtZvlc95U81142CVe5rpdpOJnmixw/exec" 

# 起動
@client.event
async def on_ready():
    print("ready")


# メッセージ受信
@client.event
async def on_message(message):
    # メッセージ送信がBOTの場合
    if message.author.bot:
        return

    Message_split = message.content.split()
    Result_Users = [0] * (len(Message_split) - 1)
    change_rate = [0] * (len(Message_split) - 1)

    # メンバーの追加
    # /push /名前M
    if Message_split[0] == '/push':
        UserName = Message_split[1]
        json_data = {
            "type" : "addUser",
            "userName" : UserName
        }
        data_encode = json.dumps(json_data)
        f = requests.post(url, data = data_encode)
        await message.channel.send("register success")


    # メンバーのレートのリスト
    # /listM
    elif Message_split[0] == '/listM':
        json_data = {
        "type" : "getUserList"
        }
        data_encode = json.dumps(json_data)
        UserList = json.loads(requests.post(url, data = data_encode).text)
        NewUserList = UserList['userList']

        # 昇順に並べ替える
        SortedUserList = sorted(NewUserList, key = lambda x : x['rating'], reverse = True)

        await message.channel.send("LIST")
        for i in range(len(SortedUserList)):
            if(SortedUserList[i]['userName'][-1] == 'M'):
                await message.channel.send(str(SortedUserList[i]['userName']) + " : " + str(round(float(SortedUserList[i]['rating']), 2)))


    # 個人戦の結果 
    # /result /1位の名前M /2位の名前M /3位の名前M ...
    elif Message_split[0] == '/result':
        for i in range(len(Message_split) - 1):
            Result_Users[i] = str(Message_split[i+1])
        json_data_get = {
            "type" : "getRating",
            "users" : Result_Users
        }
        data_encode_get = json.dumps(json_data_get)
        UserRating = json.loads(requests.post(url, data = data_encode_get).text)
        UserName_and_Rating = [{} for i in range(len(Message_split)-1)]

        # イロレーティング
        for first in range(len(Message_split) - 1):
            for second in range(len(Message_split) - 1):
                if second >  first :
                    P1_rate = float(UserRating['ratings'][first]['rating'])
                    P2_rate = float(UserRating['ratings'][second]['rating'])
                    W12 = 1 / ((10 ** ((P1_rate - P2_rate) / 400)) + 1)
                    change_rate[first] += 32 * W12
                    change_rate[second] -= 32 * W12

        for i in range(len(Message_split) - 1):
            UserName_and_Rating[i]['userName'] = Message_split[i+1]
            UserName_and_Rating[i]['rating'] = UserRating['ratings'][i]['rating'] + change_rate[i] / (len(Message_split) - 2)
        json_data_post = {
            "type" : "saveRating",
            "ratings" : UserName_and_Rating
        }
        data_encode_post = json.dumps(json_data_post)
        requests.post(url, data = data_encode_post)
        await message.channel.send("INDIVISUAL MATCH RESULT")
        for i in range(len(Result_Users)):
            await message.channel.send(str(UserName_and_Rating[i]['userName']) + " : " + str(round(float(UserName_and_Rating[i]['rating']), 2)))


    # チーム戦の結果
    # /resultT /1位チームの人数 /2位チームの人数 /3位チームの人数 ... /1位チームの名前M... /2位チームの名前M...  /3位チームの名前M... 
    elif Message_split[0] == '/resultT':
        team_number = 0
        for i in range(1, len(Message_split)):
            if Message_split[i][-1] != 'M':
                team_number += 1
            else:
                break

        Result_Users = [0] * (len(Message_split) - 1 - team_number)
        change_rate = [0] * (len(Message_split) - 1 - team_number)
        Number_of_users = (len(Message_split) - 1 - team_number)
        for i in range(len(Message_split) - 1 - team_number):
            Result_Users[i] = str(Message_split[i + 1 + team_number])
        json_data_get = {
            "type" : "getRating",
            "users" : Result_Users
        }
        data_encode_get = json.dumps(json_data_get)
        UserRating = json.loads(requests.post(url, data = data_encode_get).text)
        UserName_and_Rating = [{} for i in range(len(Message_split) - 1 - team_number)]

        team_rate = [0] * team_number
        change_team_rate = [0] * team_number

        # 各チームの合計レート
        x = 1 + team_number
        for i in range(team_number): 
            for j in range(x, x + int(Message_split[i+1])):
                team_rate[i] += float(UserRating['ratings'][j - 1 - team_number]['rating'])
            x += int(Message_split[i+1])

        # 各チームの平均レート
        for i in range(team_number):
            team_rate[i] /= int(Message_split[i+1])

        for first in range(team_number):
            for second in range(team_number):
                if second >  first :
                    W12 = 1 / ((10 ** ((team_rate[first] - team_rate[second]) / 400)) + 1)
                    change_team_rate[first] += 32 * W12
                    change_team_rate[second] -= 32 * W12

        y = 1 + team_number
        for i in range(team_number):
            for j in range(y, y + int(Message_split[i+1])):
                change_rate[j - 1 - team_number] = change_team_rate[i]
            y += int(Message_split[i+1])

        for i in range(len(Message_split) - 1 - team_number):
            UserName_and_Rating[i]['userName'] = Message_split[i + 1 + team_number]
            UserName_and_Rating[i]['rating'] = UserRating['ratings'][i]['rating'] + team_number * change_rate[i] / (len(Message_split) - 1 - team_number)
        
        json_data_post = {
            "type" : "saveRating",
            "ratings" : UserName_and_Rating
        }
        data_encode_post = json.dumps(json_data_post)
        requests.post(url, data = data_encode_post)
        await message.channel.send("TEAM MATCH RESULT")
        for i in range(len(Result_Users)):
            await message.channel.send(str(UserName_and_Rating[i]['userName']) + " : " + str(round(float(UserName_and_Rating[i]['rating']), 2)))


    # 個人戦の訂正
    # /redo
    elif Message_split[0] == '/redo':
        for i in range(len(Message_split) - 1):
            Result_Users[i] = str(Message_split[i+1])
        json_data_get = {
            "type" : "getRating",
            "users" : Result_Users
        }
        data_encode_get = json.dumps(json_data_get)
        UserRating = json.loads(requests.post(url, data = data_encode_get).text)
        UserName_and_Rating = [{} for i in range(len(Message_split) - 1)]

        for i in range(len(Message_split)-1):
            UserName_and_Rating[i]['userName'] = Message_split[i+1]
            UserName_and_Rating[i]['rating'] = UserRating['ratings'][i]['prevRating']

        json_data_post = {
            "type" : "saveRating",
            "ratings" : UserName_and_Rating
        }
        data_encode_post = json.dumps(json_data_post)
        requests.post(url,data = data_encode_post)
        await message.channel.send("REDO INDIVISUAL MATCH RESULT")
        for i in range(len(Result_Users)):
            await message.channel.send(str(UserName_and_Rating[i]['userName']) + " : " + str(round(float(UserName_and_Rating[i]['rating']), 2)))


    # チーム戦の訂正
    # /redoT
    elif Message_split[0] == '/redoT':
        team_number = 0
        for i in range(1, len(Message_split)):
            if Message_split[i][-1] != 'M':
                team_number += 1
            else:
                break

        Result_Users = [0] * (len(Message_split) - 1 - team_number)

        for i in range(len(Message_split) - 1 - team_number):
            Result_Users[i] = str(Message_split[i + 1 + team_number])
        json_data_get = {
            "type" : "getRating",
            "users" : Result_Users
        }
        data_encode_get = json.dumps(json_data_get)
        UserRating = json.loads(requests.post(url, data = data_encode_get).text)
        UserName_and_Rating = [{} for i in range(len(Message_split) - 1 - team_number)]

        for i in range(len(Message_split) - 1 - team_number):
            UserName_and_Rating[i]['userName'] = Message_split[i + 1 + team_number]
            UserName_and_Rating[i]['rating'] = UserRating['ratings'][i]['prevRating']

        json_data_post = {
            "type" : "saveRating",
            "ratings" : UserName_and_Rating
        }
        data_encode_post = json.dumps(json_data_post)
        requests.post(url,data = data_encode_post)
        await message.channel.send("REDO TEAM MATCH RESULT")
        for i in range(len(Result_Users)):
            await message.channel.send(str(UserName_and_Rating[i]['userName']) + " : " + str(round(float(UserName_and_Rating[i]['rating']), 2)))


    else:
        return


client.run(TOKEN)
