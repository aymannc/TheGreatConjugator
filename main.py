import os
import re

import PySimpleGUI as sg
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

sg.change_look_and_feel('Dark Blue 3')


def html_to_dic(html):
    html = html.replace('<br/>', "-").replace("<b>", "").replace("</b>", "")[3:-4]
    dic = html.split('-')
    result = []
    for e in dic:
        result.append(e.replace("'", " ").split(" ", 1))
    try:
        return dict((k, v) for k, v in result)
    except:
        return result


# Accessing the verbs page
file_name = "verbs_list.txt"
verb_link_list = None
if not os.path.isfile(file_name) or os.stat(file_name).st_size == 0:
    print("Searching for link list")
    url = "https://leconjugueur.lefigaro.fr/frlistedeverbe.php"
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        verbs_link = BeautifulSoup(r.text, 'html.parser').select("#pop > ul > p > a")
        verb_link_list = [("https://leconjugueur.lefigaro.fr" + link["href"]) for link in verbs_link]
        with open(file_name, "w+")as file:
            file.writelines(link + "\n" for link in verb_link_list)
else:
    with open(file_name, "r")as file:
        verb_link_list = file.read().split("\n")

# size = [8, 4, 3, 2, 2, 2, 2, 2]
collection = MongoClient().TGC.verbs
for ind, link in enumerate(verb_link_list):
    verb_name = link.split("/")[-1].split(".")[0]

    if collection.find_one({'verb': verb_name}):
        print(verb_name+" exists")
        continue
    verb = dict()
    verb["verb"] = verb_name
    r = requests.get(link)
    if r.status_code == requests.codes.ok:
        res = BeautifulSoup(r.text, "html.parser")
        verb["verb"] = link.split("/")[-1].split(".")[0]
        try:
            if ("Définition" == res.select("#Top > h3:nth-child(46)")[0].text.split(" ")[0]):
                verb["Définition"] = [e.strip() for e in
                                      re.split("[(\d)]", res.select("#Top > p:nth-child(47)")[0].text) if e != '']
        except:
            try:
                if ("Définition" == res.select("#multiple > h3:nth-child(46)")[0].text.split(" ")[0]):
                    verb["Définition"] = [e.strip() for e in
                                          re.split("[(\d)]", res.select("#Top > p:nth-child(47)")[0].text) if
                                          e != '']
            except:
                pass
            # print("Non")

        try:
            verb["Synonyme"] = [url.text for url in res.select("#Top > p:nth-child(45)")[0].find_all('a')]
        except:
            pass
        # print(res.select("#multiple > p:nth-child(45)"))
        # verb["Synonyme"] = [url.text for url in res.select("#multiple > p:nth-child(45)")[0].find_all('a') ]
        x = 0
        conj = dict()
        for i in range(len(res.select('div.modeBloc')) - 1):
            try:
                mode = res.select('div.modeBloc')[i].find('a').text
            except:
                mode = res.select('div.modeBloc')[i].find('div').h2.text
            # print(mode)
            conj[mode] = []
            size = 8 if i == 0 else 4
            for j in range(size):
                try:
                    res2 = res.select('div.conjugBloc')[x + j]
                    time = str(res2.find('div').p.text)
                    html = str(res2.find_all('p')[1])
                except:
                    break
                all_times = dict()
                all_times[time] = (html_to_dic(html))
                # print("all :", all_times)
                conj[mode].append(all_times)
            x += size
            # print("mode ", mode, conj[mode])
        verb["conj"] = conj
        # Save the verb to a file for now
        # base_dic = "verbs/"
        # os.makedirs(os.path.dirname(base_dic), exist_ok=True)
        # with open(base_dic + verb["verb"] + ".txt", "w+")as file:
        #     file.write(json.dumps(verb, indent=4, sort_keys=True, ensure_ascii=False))

        # Saving it on the MongoDB
        if collection.insert_one(verb).inserted_id:
            print(link)

    else:
        print(F"Couldn't get {link}")

    if not sg.OneLineProgressMeter('Processing ', ind + 1, len(verb_link_list), 'key', 'Getting verbs data',
                                   orientation='horizontal'): break
