#!/usr/bin/env python3
import os
import sys
import csv
import datetime
import re
#####################################################
#Dockerfileのパスを取得
#Dockerfile_Pass = input("キャッシュの組み換えを行うDockerfileが存在するディレクトリのパスを入力して下さい:")
Dockerfile_Pass = "/home/c0a20028/_dockerripo/doge-unblocker"
#Dockerfile_Pass = "/home/c0a20028/_dockerripo/SneakerBot-master"
#####################################################
file_name = Dockerfile_Pass.split('/')
file_name = file_name[-1]
tmp_list = []
#####################################################
#DockerfileのCOPY行を抽出
with open(Dockerfile_Pass+"/Dockerfile", newline='', mode='r') as f:
    Dockerfile_Command = f.readlines()
Dockerfile_COPY = []
for row in Dockerfile_Command:
    if ("COPY" in row):
        Dockerfile_COPY.append(row)
#.dockerignoreのリストを抽出
try:
    with open(Dockerfile_Pass+"/.dockerignore", newline='', mode='r') as f:
        dockerignore = f.read().splitlines()
except:
    dockerignore = []
#####################################################
#COPYするファイルのリストを作成
#このソフトウェアが分散させたファイルを.memから取得
try:
    with open(file_name+".mem", mode='r', newline='') as f:
        writed_command = f.readlines()
except:
    writed_command = []
#####################################################
#COPYからファイル名抽出
#複数コピーがあるかチェック
Dockerfile_COPY_DIR = [] #コピー元
Dockerfile_COPY_to = [] #コピー先
is_multicopy = 0
for row in Dockerfile_COPY:
    row = row.replace('\r\n', '')
    #print(row)
    #このプログラムが書いたコマンドは除外する
    if(row in writed_command):
        continue
    else:
        row = row.split()
        #一部の特殊文字を無視する
        for row_length in range(len(row)):
            row[row_length] = row[row_length].replace("[","")
            row[row_length] = row[row_length].replace("]","")
            row[row_length] = row[row_length].replace('"','')
            row[row_length] = row[row_length].replace(',','')
        tmp_list = []
        for length in range(len(row)-2):
            tmp_list.append(row[length+1])
        if(row[-1] == "./"):
            row[-1] = "."
        Dockerfile_COPY_to.append(row[-1])
        Dockerfile_COPY_DIR.append(tmp_list)
        #1ファイルのみのコピーかチェック
        if not((len(row)<=3) and (os.path.isfile(Dockerfile_Pass+"/"+row[1]))):
            is_multicopy += 1
if (is_multicopy == 0):
    print("複数コピーする行が存在しません。")
    print("プログラムを終了します。")
    sys.exit()
#####################################################
#COPYするのがディレクトリならば、その中身を羅列する
#print(Dockerfile_COPY_DIR)
Dockerfile_COPY_LIST = []
COPY_LIST = []
COPY_LIST_FLAG = [] #0=file 1~=dir
i = 0
for row2 in Dockerfile_COPY_DIR:
    tmp_list = []
    COPY_LIST_FLAG.append(0)
    for row in row2:
        #一部の特殊文字を無視する
        row = row.replace("[","")
        row = row.replace("]","")
        row = row.replace('"','')
        row = row.replace(',','')
        if(os.path.isfile(Dockerfile_Pass+"/"+row)):
            tmp_list.append(Dockerfile_COPY_to[i]+"/"+row)
        else:
            tmp_list = os.listdir(Dockerfile_Pass+"/"+row)
            COPY_LIST_FLAG[i] += 1
            #ディレクトリが無くなるまで中身を取り出す
            while True:
                dir_count=0
                for file in tmp_list:
                    if(os.path.isdir(Dockerfile_Pass+"/"+file)):
                        dir_count+=1
                        tmp_list.remove(file)
                        dir_in_file=[]
                        dir_in_file.extend(os.listdir(Dockerfile_Pass+"/"+row+"/"+file))
                        for dir_file in dir_in_file:
                            tmp_list.append(os.path.relpath(Dockerfile_Pass+"/"+row+"/"+file+"/"+dir_file,Dockerfile_Pass))
                if(dir_count==0):
                    break
            #"COPY . ."でなければ、先頭に"./"を足さないと./で揃わなくなる
            if(row == "."):
                for j in range(len(tmp_list)):
                    tmp_list[j] = Dockerfile_COPY_to[i]+"/"+tmp_list[j]
            else:
                for j in range(len(tmp_list)):
                    tmp_list[j] = "./"+Dockerfile_COPY_to[i]+"/"+tmp_list[j]
    COPY_LIST.append(tmp_list)
        #"COPY . ."の場合、既にコピーしているものを除外する
    if(row == "."):
        already_in_list = []
        for already in Dockerfile_COPY_LIST:
            already_in_list.extend(already)
        COPY_LIST[i] = list(set(COPY_LIST[i])-set(already_in_list))
        #COPYリストから、Dockerignoreしてるファイルを除外
        #ハードコーディング(#･∀･)
        #match = [s for s in COPY_LIST[i] if re.match("./"+dockerignore[3], s)]
        #for ignore in match:
        #    COPY_LIST[i].remove(ignore)
    Dockerfile_COPY_LIST.append(COPY_LIST[i])
    i += 1
#####################################################
#外部にあるCSVファイルを読み込み、更新回数リストを作成
with open(file_name+".csv", newline='', mode='r') as f:
    reader = csv.reader(f)
    Update_count = [row for row in reader]
#####################################################
#各ファイルの更新回数を記したリストを作成
Update_count_list_next = []
for i in range(len(Dockerfile_COPY_LIST)):
    if(int(COPY_LIST_FLAG[i])!=0):
        tmp_list = []
        for index in range(len(Update_count)):
            for file in range(len(Dockerfile_COPY_LIST[i])):
                if((Dockerfile_COPY_LIST[i][file] == Dockerfile_COPY_to[i]+"/"+Update_count[index][0]) or (Dockerfile_COPY_LIST[i][file] == "./"+Update_count[index][0])):
                
                    file_Update_count = 0
                    for count in range(len(Update_count[index])):
                        if(count==0):
                            continue
                        file_Update_count += int(Update_count[index][count])
                    tmp_list.append([Update_count[index][0],file_Update_count])
        Update_count_list_next.append(tmp_list)
#初回で無いなら、前回の実行日までと今回の実行日の両方作成する
Update_count_list_last = []
if(Update_count[0][0]!=""):
    Run_date = Update_count[0][0]
    Update_count[0][0] = ""
    Run_date_index = Update_count[0].index(Run_date)
    for i in range(len(Dockerfile_COPY_LIST)):
        if(int(COPY_LIST_FLAG[i])!=0):
            tmp_list = []
            for index in range(len(Update_count)):
                for file in range(len(Dockerfile_COPY_LIST[i])):
                    if((Dockerfile_COPY_LIST[i][file] == Dockerfile_COPY_to[i]+"/"+Update_count[index][0]) or (Dockerfile_COPY_LIST[i][file] == "./"+Update_count[index][0])):   
                        file_Update_count = 0
                        for count in range(Run_date_index):
                            if(count==0):
                                continue
                            file_Update_count += int(Update_count[index][count])
                        tmp_list.append([Update_count[index][0],file_Update_count])
            Update_count_list_last.append(tmp_list)
    Update_count[0][0] = Run_date
#更新回数が1のファイルを抽出
Update_count_list_last_1 = []
Update_count_list_next_1 = []
for j in range(len(Update_count_list_last)):
    #前回の更新回数が1のみのファイルを抽出
    tmp_list = []
    for i in range(len(Update_count_list_last[j])):
        if(int(Update_count_list_last[j][i][1])==1):
            tmp_list.append(Update_count_list_last[j][i])
    Update_count_list_last_1.append(tmp_list)
    #現在の更新回数が1のみのファイルを抽出
    tmp_list = []
    for i in range(len(Update_count_list_next[j])):
        if(int(Update_count_list_next[j][i][1])==1):
            tmp_list.append(Update_count_list_next[j][i])
    Update_count_list_next_1.append(tmp_list)
#前回と今回の間に、更新回数が0→1か1→2してるファイルが無い場合、中断する
if(Update_count_list_last_1 == Update_count_list_next_1):
    print("低頻度の更新ファイルに更新はありません。")
    print("プログラムを終了します。")
    sys.exit()
#####################################################
#元のCOPY行改変と、新COPY行作成
#新しいCOPY行を作る
new_command_list = []
for i in range(len(Update_count_list_next_1)):
    if not(Update_count_list_next_1[i]):
        continue
    new_command = "COPY"
    for row in Update_count_list_next_1[i]:
        new_command += " " + str(row[0])
    new_command += " " + Dockerfile_COPY_to[i]
    new_command_list.append(new_command)
#作成したCOPY行をDockerfile_Commandに記述
for j in range(len(new_command_list)):
    for i in range(len(Dockerfile_Command)):
        if (str(Dockerfile_Command[i]) in new_command_list[j] + "\r\n"):
            Dockerfile_Command[i]=new_command_list[j] + "\r\n"
            break
        #elif ("WORKDIR" in str(Dockerfile_Command[i])):
        elif (str(Dockerfile_Command[i]) in "COPY . .\r\n"):
            Dockerfile_Command.insert(i,new_command_list[j] + "\r\n")
            break
        elif (str(Dockerfile_Command[i]) in str(Dockerfile_COPY[j])):
            #Dockerfile_Command.insert(i+1,new_command_list[j] + "\r\n")
            #break
            continue
#####################################################
#元Dockerfileのバックアップ、Dockerfile_CommandをDockerfile化
"""
dt_now = datetime.datetime.now()
os.rename(Dockerfile_Pass+"/Dockerfile",Dockerfile_Pass+"/Dockerfile_"+dt_now.strftime('%Y%m%d')+".backup")
"""

with open(Dockerfile_Pass+"/Dockerfile", mode='w', newline='') as f:
    f.writelines(Dockerfile_Command)

"""
#このプログラムが書いたコマンドを記憶する
with open(file_name+".mem", mode='w', newline='') as f:
    f.writelines(new_command)
#実行日を記憶
Update_count[0][0]=Update_count[0][-1]
with open(file_name+".csv", mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(Update_count)
"""
#####################################################
print("Done.")