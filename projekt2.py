# -*- coding: utf-8 -*-

import json,urllib,io,matplotlib,numpy,os,optparse,time,pymongo
from pymongo import MongoClient
from pylab import *

def getData(link):
    '''
    Pobiera dane z serwera i laduje do jsona
    '''
    answer=urllib.urlopen(link)
    data=json.loads(answer.read())
    answer.close()
    return data

def getClient():
    '''
    Wyciaga klienta do bazy programu - last_db
    '''
    return MongoClient().last_db
     

def getUsers(nameGr,number): 
    users=[]
    '''
    Pobieranie listy uzytkownikow wg nazwy grupy i ilosci uzytkonikow dla ktorych pobieramy dane, zwraca json z uzytkownikami
    '''
    data=getData("http://ws.audioscrobbler.com/2.0/?method=group.getmembers&api_key=ea9c1eefc7efdcbd04395f01f6c138f3&format=json&group=%s&limit=%s"%(nameGr,number))
    db = getClient()
    usersName=db['usersName']
    usersName.remove()
    usersName.insert(data)
    result=[]
    for element in usersName.find():
        user=element['members']['user']
        for u in user:
            result.append(u['name'])
    print "Pobrano liste uzytkownikow..."
    return result

def getTopFan(artist): 
    '''
    Pobieranie listy top fanow danego artysty, zwraca json z uzytkownikami
    '''
    data=getData("http://ws.audioscrobbler.com/2.0/?method=artist.gettopfans&api_key=ea9c1eefc7efdcbd04395f01f6c138f3&format=json&artist=%s" %artist)
    db = getClient()
    topFan=db['topFan']
    topFan.remove()
    topFan.insert(data)
    result=[]
    for fan in topFan.find():
        user = fan['topfans']['user']
        for u in user:
            result.append(u['name'])
    print "Pobrano liste uzytkownikow..."
    return result

def getUsersInfo(userList): 
    '''
    Pobieranie informacji o poszczegolnym uzytkowniku, wejsciowe dane to json z uzytkownikami
    '''
    db = getClient()
    info=db['info']
    info.remove()
    print "Rozpoczeto przetwarzanie danych..."
    curTime=time.time()
    startTime=curTime
    for i in xrange(0,len(userList)):
        data=getData("http://ws.audioscrobbler.com/2.0/?method=user.getinfo&api_key=ea9c1eefc7efdcbd04395f01f6c138f3&format=json&user=%s" %userList[i])
        info.insert(data)       
        if time.time()-curTime>=20:
            print "Przetwarzam dane..."
            curTime=time.time()
    elapsedTime=time.time()-startTime
    min=elapsedTime/60
    sec=elapsedTime-int(elapsedTime/60)*60
    print "Dane przetworzono w czasie: %.0f m %2.2f s." %(min,sec)
    result=[]
    for element in info.find():
        result.append(element['user']['country'])
    return result

def getRecomendationFromGroup(nameGr): 
    '''
    Pobiera liste artystow rekomendowanych wg popularnosci artysty w danej grupie
    '''
    recomend=[]
    data=getData("http://ws.audioscrobbler.com/2.0/?method=group.getweeklyartistchart&api_key=ea9c1eefc7efdcbd04395f01f6c138f3&format=json&group=%s" %nameGr)
    db = getClient()
    recommendation=db['recommendation']
    recommendation.remove()
    recommendation.insert(data)
    for element in recommendation.find():
        artist=element['weeklyartistchart']['artist']
        for a in artist:
            recomend.append(a['name'])
    return recomend

def getTopArtist(userList):
    '''
    Pobiera topowych artystow uzytkownikow w grupie do bazy danych
    '''
    db = getClient()
    topArtist=db['topArtist']
    topArtist.remove()
    print "Rozpoczeto przetwarzanie danych o podobnych artystach..."
    curTime=time.time()
    startTime=curTime
    for i in xrange(0,len(userList)):
        data=getData("http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&api_key=ea9c1eefc7efdcbd04395f01f6c138f3&format=json&user=%s" %userList[i])
        topArtist.insert(data)       
        if time.time()-curTime>=20:
            print "Przetwarzam dane..."
            curTime=time.time()
    elapsedTime=time.time()-startTime
    min=elapsedTime/60
    sec=elapsedTime-int(elapsedTime/60)*60
    print "Dane przetworzono w czasie: %.0f m %2.2f s." %(min,sec)
    return 

def getRecommendationFromTopArtist():
    '''
    Liczy rekomendacje na bazie topArtystow, ktorych pobiera z bazy
    '''
    db = getClient()
    topArtist=db['topArtist']
    count=0
    result=[]
    dict1={}
    dict2={}
    for element in topArtist.find():
        if count==0:
            artist=element['topartists']['artist']
            value=len(artist)
            for a in artist:
                dict1.update({a['name']:value})
                value=value-1
            count=count+1
        elif count==1:
            artist=element['topartists']['artist']
            value=len(artist)
            for a in artist:
                dict2.update({a['name']:value})
                value=value-1
            artists1=dict1.keys()
            artists2=dict2.keys()
            for a1 in artists1:
                if a1 in artists2:
                    result.append([a1,dict1[a1]+dict2[a1]])
                else:
                    result.append([a1,dict1[a1]])
            count=count+1
        else:
            dict2={}
            artist=element['topartists']['artist']
            value=len(artist)
            for a in artist:
                dict2.update({a['name']:value})
                value=value-1       
            artists2=dict2.keys()
            art1=result[:][0]
            for artist2 in artists2:
                if artist2 in art1:
                    ind=result.index(art1)
                    result.insert(ind,[artist2,dict2[artist2]+result[ind][1]])
                else:
                    result.append([artist2,dict2[artist2]])
    return result

def getMaxOfList(list,number):
    '''
    Sortuje wynik z getRecommendationFromTopArtist od maksymalnego do minimalnego, wybiera tylko ilosc "number" pierwszych polecanych
    '''
    result=[]
    values=[]
    names=[]
    for i in xrange(0,len(list)):
        for k in xrange(0,len(list)):
            values.append(list[k][1])
            names.append(list[k][0])
        maxValue=max(values)
        ind=values.index(maxValue)
        result.append(names[ind])
        list.remove([names[ind],maxValue])
        if i==number:
            break
        del values[:]
        del names[:]
    return result 
        
def getSimilar(artist): 
    ''''
    Pobiera liste artystow podobnych do artysty podanego na wejsciu
    '''
    similar=[]
    db = getClient()
    data=getData("http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&api_key=ea9c1eefc7efdcbd04395f01f6c138f3&format=json&artist=%s" %artist)
    similarA=db['similarA']
    similarA.remove()
    similarA.insert(data)
    for element in similarA.find():
        artist=element['similarartists']['artist']
        for a in artist:
            similar.append(a['name'])
    return similar

def getStatistics(data,number):  
    '''
    Liczy statystki, zwraca liste: nazwa i procent 
    '''
    country=[]
    for d in range(0,len(data)):
        country.append(data[d])
    count=set(country)
    stat=[]
    for i in count:
        s=[i,(float(country.count(i))*float(100.0)/float(number))]
        stat.append(s)
    return stat 

def getMax(list):  
    '''
    Wybiera maksymalna wartosc ze statystyk z getStatistics
    '''
    list1=[]
    list2=[]
    for element in list:
        list1.append(element[0])
        list2.append(element[1])
    m=max(list2)
    int=list2.index(m)
    return [list1[int],m]

def getColor(number): 
    '''
    pobieranie kolorw do wykresu
    '''
    colors=[]
    for i in xrange(0,number):
        c=randint(30,16777215)
        colors.append("#%06x" %c)    
    return colors

def drawChart(data):  
    '''
    Rysowanie piechart, jezeli wartosci sa mniejsze niz 2% wrzucam je do jednego kawalka (inne)
    '''
    figure(1, figsize=(7,7))
    fracs=[]
    labels=[]
    other=0
    for element in data:
        if float(element[1])<2:
            other=other+float(element[1])
        else:
            fracs.append(element[1])
            if " " in element[0]:
                element_s=element[0].split(" ")
                element_s[0]=element_s[0]+"\n"
                element[0]=element_s[0]+element_s[1]
            labels.append(element[0])
    if other!=0:
        fracs.append(other)
        labels.append("inne")
    colors=getColor(len(fracs))
    pie(fracs, labels=labels,colors=colors,
                autopct='%1.2f%%', shadow=False, startangle=90)
    title('Rozklad uzytkownikow wg kraju pochodzenia')
    show()
    return 

def setCountryPLName(data): 
    '''
    Pobiera dane z pliku tekstowego cpuntries.txt i przypisuje polskie nazwy do skrotow ISO, ktore sa wynikiem zapytan do serwera
    '''
    countries={}
    file=open('countries.txt','r')
    text=file.readlines()
    for line in text:
        spl=line.split(",")
        countries.update({spl[0]:spl[1]})
    file.close()
    countries.update({"":"brak informacji"})
    shorts=countries.keys()
    for element in data:
        for short in shorts:
            if str(element[0]) == str(short):
                element[0]=countries[short]
    return data   

def printRecomendation(artists):
    '''
    Drukuje na konsoli tablice 30 artystow i pyta sie czy wyswietlic wiecej
    '''
    for artist in artists:
        if artists.index(artist)==30:
            odp = raw_input("\n\nWyswietlono 30 artystow, czy kontynuowac wyswietlanie?\nt - tak, downolny znak - wyjscie z programu. ")
            if odp=='t':
                if artists.index(artist)%10==0:
                    try:
                        print "\n"+ unicode(artist)+", ",
                    except ValueError:
                        print "[nieprawidlowa nazwa]"
                else: 
                    try:
                        print unicode(artist)+", ",
                    except ValueError:
                        print "[nieprawidlowa nazwa]"
            else:
                exit(-1)
        else:
            if artists.index(artist)%10==0:
                try:
                    print "\n"+ unicode(artist)+", ",
                except ValueError:
                    print "[nieprawidlowa nazwa]"
            else: 
                try:
                    print unicode(artist)+", ",
                except ValueError:
                    print "[nieprawidlowa nazwa]"
                    
                    
def printOwnRecommendation(artists):
    for artist in artists:
        if artists.index(artist)%10==0:
            try:
                print "\n"+ unicode(artist)+", ",
            except ValueError:
                print "[nieprawidlowa nazwa]"
        else: 
            try:
                print unicode(artist)+", ",
            except ValueError:
                print "[nieprawidlowa nazwa]"

def printOutput(result):
    '''
    Drukuje na konsoli wynik z getStatistics
    '''
    for list in result:
        if str(list[0])!="brak informacji":
            print "uzytkownicy z kraju %s to %s %% uzytkownikow," %(str(list[0]).replace('\n', ''),str(list[1]))
        else: 
            print "%s %% uzytkownikow nie uzupelnilo informacji o kraju z ktorego pochodza," %str(list[1])
    if  str(getMax(result)[0])!="brak informacji":
        print "\ndlatego wlasnie z %s %% prawdopodobienstwem jestes z kraju %s" %(str(getMax(result)[1]),str(getMax(result)[0]))
    else:
        print "\ndlatego wlasnie z %s %% prawdopodobienstwem nie uzupelnisz profilu o informacje z jakiego kraju pochodzisz :)" %str(getMax(result)[1])




def main():
    '''
    Glowna funkcja programu
    '''
    parser = optparse.OptionParser()
    parser.add_option("-g",'--group',help='Wpisz nazwe grupy z last.fm do ktorej chcesz dolaczyc, a dowiesz sie czegos o sobie.',dest='f_group',nargs=2,type='string',metavar='<nazwa grupy>,<liczba uzytkownikow>')
    parser.add_option("-a",'--artist',help="Wpisz nazwe artysty, ktorego lubisz.",dest='f_artist',nargs=1,type='string',metavar='<nazwa artsty>')
    (opts, args) = parser.parse_args()
    
    if opts.f_group:
        name=opts.f_group[0]
        number=opts.f_group[1]
        if number=='1':
            print "%s to zla liczba uzytkownikow do pobrania statystyk, sprobuj jeszcze raz." %number
        else:
            try:
                userList=getUsers(name,number)
                result=setCountryPLName(getStatistics(getUsersInfo(userList),int(number)))
                print "\nW grupie %s jest nastepujacy rozklad uzytkownikow:\n" %name
                printOutput(result)
                print "Zamknij wykres aby kontynuowac..."
                drawChart(result)
                artists=getTopArtist(userList)
                try:
                    data=getRecommendationFromTopArtist()
                    result2=getMaxOfList(data,30)
                    print "\nArtysci, ktorych mozesz lubic (na bazie topowych artystow dla uzytkownikow w grupie):"
                    printOwnRecommendation(result2)
                except:
                    print "\nNie udalo sie wyswietlic rekomendacji na bazie topArtist"
                print "\n\nArtysci, ktorych mozesz lubic (najczesciej sluchani w wybranej grupie): "
                recommendation=getRecomendationFromGroup(name)
                printRecomendation(recommendation)
            except (KeyError,TypeError):
                print "Nie udalo sie pobrac danych dla grupy %s, sprawdz czy nazwa grupy jest prawidlowa." %name
            except ValueError:
                print "%s to zla liczba uzytkownikow do pobrania statystyk." %number
            except IOError:
                print "Nie udalo sie nazwiazac polaczenia z serwerem, sprawdz argumenty zapytania."
            exit(-1)
      
    if opts.f_artist:
        artist=opts.f_artist
        try:
            userList=getTopFan(artist)
            data=getUsersInfo(userList)        
            result=setCountryPLName(getStatistics(data,len(data)))
            print "\nStatystyki dla topFanow %s \n" %opts.f_artist
            printOutput(result)
            print "\nZamknij wykres aby kontynuowac..."
            drawChart(result)
            artists=getTopArtist(userList)
            try:
                data=getRecommendationFromTopArtist()
                result2=getMaxOfList(data,30)
                print "\nArtysci, ktorych mozesz lubic (na bazie topowych artystow dla topFanow):"
                printOwnRecommendation(result2)
            except:
                print "\nNie udalo sie wyswietlic rekomendacji na bazie topArtist"
            print "\n\nArtysci, ktorych mozesz takze lubic (podobni do tego ktorego wybrales): "
            try:
                similar=getSimilar(artist)
                printRecomendation(similar)
            except TypeError:
                print "Nie udalo sie pobrac podobnych artystow."
        except KeyError:
            print "Wpisany artysta nie istnieje w bazie last.fm."
        exit(-1)

if __name__ == "__main__":    
    main()    

