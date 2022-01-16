import pandas as pd
import spacy
import es_core_news_sm
from spacy.matcher import Matcher
from scipy import spatial
import re
import math
import unicodedata
import unidecode
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from operator import itemgetter


PREGUNTAS = {
    #IDIOMAS 4
    '¿Qué idiomas habla?':4, '¿Qué idiomas conoce el candidato?': 4,
    '¿Cuáles son los idiomas que conoce el candidato?': 4, '¿Qué lenguas habla el candidato?': 4,
    '¿Qué lenguas son las que conoce el candidato?': 4, '¿Que idiomas habla?': 4,
    #Nombre del candidato 0
    '¿Cómo se llama el candidato?': 0, '¿Cuál es el nombre del candidato?:': 0,
    '¿Cómo se llama el candidato?': 0, '¿Con qué nombre responde el candidato?': 0,
    '¿Quién es el candidato?': 0, 'Nombre del candidato': 0,
    #Teléfono del candidato 2
    '¿Cuál es el número de teléfono del candidato?': 2, '¿Qué número de teléfono tiene el candidato?': 2,
    '¿A qué número hay que llamar para contactar con el candidato?': 2, '¿Qué número de teléfono figura como el número del candidato?': 2,
    '¿Teléfono de contacto?': 2, '¿Cual es teléfono móvil?':2,

    #Experiencia laboral 7
    '¿Qué experiencia laboral tiene?': 7, '¿Qué experiencia tiene el candidato?': 7,
    '¿Cuál es la experiencia que tiene el candidato?': 7, '¿Qué tipo de experiencia tiene el candidato?':7,
    '¿Dónde ha trabajado previamente el candidato?': 7, '¿Qué profesiones ha llevado a cabo previamente el candidato?': 7,
    '¿Experiencia?': 7, 'Donde ha trbbajado?:':7,
    #Lengiajes de programación 3
    '¿Qué lenguajes de programación conoce?': 3, '¿Qué lenguajes de programación controla el candidato?':3,
    '¿Cuáles son los lenguajes de programación que controla el candidato?': 3, '¿Cómo se llaman los lenguajes de programación que controla el candidato?': 3,
    '¿De qué lenguajes de programación tiene conocimientos el candidato?':3, '¿Lenguajes de programación?': 3, '¿Sabe progrmar en Python?': 3, 'Conoce Java': 3,
    #Formación académica 6
    '¿Qué educación tiene el candidato?': 6, '¿Qué títulos tiene el candidato?': 6,
    '¿Cuáles son los títulos del candidato?':6, '¿Con qué titulaciones cuenta el candidato?': 6,
    '¿Qué ha estudiado?': 6, '¿Qué estudios tiene?': 6,
    #Correo de contacto 1
    '¿Cuál es su correo de contacto?':1, '¿Cuál es el correo del candidato?': 1,
    '¿Qué correo tiene el candidato?': 1, '¿A qué dirección de correo debemos escribir para contactar con el candidato?': 1,
    '¿Qué dirección de correo figura como la dirección del candidato?': 1, '¿Correo?': 1, 'email?':1,'¿email del candidato?': 1, '¿e-mail?':1,
    #Referencias 5
    '¿Cuáles son sus referencias?': 5, '¿Cuáles son las referencias del candidato?': 5,
    '¿Qué referencias tiene el candidato?': 5, '¿Qué personas pueden servir como referencia del candidato?': 5,
    '¿Quién figura como referencia del candidato?': 5, '¿Referencias?' : 5
}

secciones = ['EXPERIENCIA', 'EDUCACIÓN', 'CONTACTO', 'HABILIDADES', 'IDIOMAS', 'REFERENCIAS']

# Extracción de secciones:


def encontrar_seccion(seccion, df):
    fila_i = None
    fila_f = None
    for f in range(len(df['text'])):
        if seccion in df['text'][f]:
            fila_i = f
        v = [l.isupper() for l in df['text'][f].strip('\n')]
        if fila_i != None and all(v) and f!= fila_i and len(v) != 0:
            fila_f = f
            break
    return (fila_i, fila_f)

def saca_texto(lineas):
    i, f = lineas
    texto = ''
    for j in range(i, f):
        texto += df['text'][j]
    return texto

def encontrar_idiomas(df):

    tokenizer = RegexpTokenizer(r'[0-9A-Za-z_À-ÿñ]{2,}')
    palabras_vacias = set(stopwords.words('spanish'))

    relevantes = ['Español','A1','A2','B1','B2','C1','C2','Alemán','Francés', 'Inglés', 'English'
     'Italiano', 'Chino', 'Ruso', 'Japonés', 'Portugués', 'Catlán', 'Català', 'Vasco', 'Euskera', 'Euskara',
     'Gallego', 'Galego']
    limpio_relevantes = []
    for x in relevantes:
        limpio_relevantes.append(limpiar_pregunta(x))

    idiomas = '\n'
    for f in range(len(df['text'])):

        frase = df['text'][f]
        #print(frase)
        frase = limpiar_pregunta(frase)
        frase =  tokenizer.tokenize(frase)
        #print(frase)
        frase = [w for w in frase if not w.lower() in palabras_vacias]

        if len(set(limpio_relevantes).intersection(set(frase))) > 0 :
            idiomas += df['text'][f] + '\n'

    if len(idiomas) < 3:
        return "No hemos encontrado información de idiomas"


    return idiomas

# print(saca_texto(encontrar_seccion(secciones[0])))

# Extracción del nombre del candidato:

def encontrar_nombre(x, df):
    nlp = es_core_news_sm.load()
    doc = nlp(x)
    matcher = Matcher(nlp.vocab)
    matcher.add("matching_father", pattern_father)
    matches = matcher(doc)
    sub_text = ''
    if(len(matches) > 0):
        span = doc[matches[0][1]:matches[0][2]]
        sub_text = span.text
    tokens = sub_text.split(' ')

    if len(tokens) == 3:
        name, surname1, surname2 = tokens[0], tokens[1], tokens[2]
    else:
        name, surname1, surname2 = None, None, None
    return name, surname1, surname2

def devolver_nombre(df):
    nombre = None
    for f in range(len(df['text'])):
        if df['Nombre'][f] != None and df['Apellido1'][f] != None and df['Apellido2'][f] != None:
            if f == 0:
                nombre = df['Nombre'][f] + ' ' + df['Apellido1'][f] + ' ' + df['Apellido2'][f]
    return nombre

last_token = ['\n']

pattern_father = [[{'POS':'PROPN', 'OP' : '+'},
           {'POS':'PROPN', 'OP' : '+'},
           {'POS':'PROPN', 'OP' : '+'},
           {'LOWER': {'IN' : last_token}}]]


# Extracción de lenguajes de programación:

def encontrar_lenguajes(df):
    lenguajes = 'Python, R, Java, C, JavaScript, Matlab, SQL, SPARQL, C++'
    punto = None
    fila = None
    for f in range(len(df['text'])):
        if 'lenguajes de programación' in df['text'][f].lower():
            fila = f
            punto = df['text'][f].lower().index('lenguajes')
            break
    cadena = df['text'][fila][punto:].replace(',','').replace('.','').split()
    l = [i for i in cadena if i in lenguajes.replace(',','').split()]
    return ', '.join(l)

def tf_idf(frase, idf, union, k):

    tokenizer = RegexpTokenizer(r'[A-Za-z_À-ÿñ]{3,}')
    palabras_vacias = set(stopwords.words('spanish'))

    tf = dict.fromkeys(union,0)
    tf_idf = dict.fromkeys(union,0)
    #TF
    frase_tokens = tokenizer.tokenize(frase)
    frase_tokens = [w for w in frase_tokens if not w.lower() in palabras_vacias]

    for palabra in frase_tokens:
        tf[palabra] += 1

    for palabra in frase_tokens:
        tf_idf[palabra] = idf[palabra] * tf[palabra]

    l = sorted(tf_idf.items(), key=itemgetter(1), reverse=True)
    l = l[:k]
    #Compute array
    arr = []
    for palabra in union:
        match = False
        for par in l:
            if palabra == par[0]:
                match = True
                break
        if match:
            arr.append(1)
        else:
            arr.append(0)
    return arr

def limpiar_pregunta(cadena):
    cadena_procesada = unidecode.unidecode(cadena)  #Quitar acentos
    cadena_procesada = cadena_procesada.lower()  # A minúsculas
    cadena_procesada = cadena_procesada.replace('(','').replace(')','').replace('[','').replace(']','')
    cadena_procesada = re.sub(r"[^a-z0-9 ñ]", "",cadena_procesada) #Quitar  carácteres especiales

    return cadena_procesada

#Tomar una pregunta y buscar la más similar
def preocesar_pregunta(pregunta):

    tokenizer = RegexpTokenizer(r'[A-Za-z_À-ÿñ]{3,}')
    palabras_vacias = set(stopwords.words('spanish'))

    #Preprocesar pregunta:
    pregunta_procesada = limpiar_pregunta(pregunta)
    texto =  ''

    #Si la pregunta esta vacía tras procesar:
    if len(pregunta_procesada)<4:
        return ['', '',0]

    #Corpus de preguntas
    for q in PREGUNTAS:
        #Si está en la lista, terminamos aquí
        if ( pregunta_procesada in limpiar_pregunta(q) ) or ( limpiar_pregunta(q) in pregunta_procesada ):
            return [q, PREGUNTAS[q], 1]

        q_procesada = limpiar_pregunta(q) + ' '
        texto += q_procesada

    #Miramos si la pregunta está relacionada con la base de datos de preguntas
    texto = tokenizer.tokenize(texto)
    texto = [w for w in texto if not w.lower() in palabras_vacias]

    palabras_pregunta = tokenizer.tokenize(pregunta_procesada)
    palabras_pregunta = [w for w in palabras_pregunta if not w.lower() in palabras_vacias]

    if(len( set(texto).intersection(set(palabras_pregunta)) )<1):
        return ['','',0]

    for palabra in palabras_pregunta:
        texto.append(palabra)
    #IDF
    N = len(texto)
    union = set(texto)

    #print('Union  '+str(union))

    IDF = dict.fromkeys(union,0)
    for palabra in texto:
        IDF[palabra] += 1

    for palabra in texto:
        IDF[palabra] = math.log10((N/(1+IDF[palabra])))
    #Buscamos la frase más cercana
    v1 = tf_idf(pregunta_procesada, IDF, union, 15)
    max = 0
    cercana = []
    for q in PREGUNTAS:
        q_procesada = limpiar_pregunta(q)
        v2 = tf_idf(q_procesada, IDF, union, 15)
        d = 1 - spatial.distance.cosine(v1, v2)
        if d > max:
            max = d
            cercana = [q, PREGUNTAS[q], d]

    return cercana

def preguntar_pregunta(pregunta):
        #Cotas de similitud:
        cota1 = 0.95
        cota2 = 0.6
        vector = preocesar_pregunta(pregunta)
        print("\nEstamos seguros con score = "+str(vector[2])+" de que la pregunta es:\n"+str(vector[0])+"\n")
        if vector[2] >= cota1:
            selector = vector[1]
        elif vector[2] >= cota2:
            selector = vector[1]
            print("\n¿Es esta su pregunta: (s/n)?\n")
            print("\n"+vector[0]+"\n")
            confirm = input()
            if not confirm.lower() == 's' and not confirm.lower() == 'si' and not confirm.lower() == 'sí':
                selector = -1
        else:
            print("\nLo siento, no le entiendo\n")
            selector = -1

        return selector


def main():
    parada = False
    while (not parada):
        # Elección del CV a analizar
        rutas = ["cv_txt/cv_jorge.txt", "cv_txt/cv_luis.txt"]

        indice = input(("Escriba 0 para elegir el primer currículum, "
        "1 para elegir el segundo currículum o "
        "cualquier otra cosa para salir del sistema de preguntas:\n"))

        if indice.isdigit():
            if int(indice) not in range(2):
                print("GRACIAS por hacer uso de este servicio. Le esperamos cuando tenga alguna duda.")
                parada = True
                break
            else:
                indice = int(indice)
        else:
            print("Gracias por hacer uso de este servicio. Le esperamos cuando tenga alguna duda.")
            parada = True
            break

        fichero = rutas[indice]

        #Cambiamos la variable pregunta para elegir qué dato tomamos
        # Las preguntas está hechas de esta forma hasta que sepamos qué preguntas base y qué parafraseo poner.
        # Los números llegan hasta el 7, que son las dimensiones que tenemos actualmente.
        # Si queremos añadir más solo habría que aumentar el range

        pregunta = input(("\n\n¿Qué quieres saber sobre el candidato? \n\n"))

        selector = preguntar_pregunta(pregunta)
        print(selector)

        while selector not in range(8):
            pregunta = input(("\n\n¿Qué quieres saber sobre el candidato? \n\n"))
            selector = preguntar_pregunta(pregunta)
            print(selector)


        # Procesamiento del txt

        with open(fichero, 'r') as f:
            text = [line for line in f.readlines()]

        df = pd.DataFrame(text,columns=['text'])

        df.head()

        #print("\n df = \n"+str(df))

        text = df['text'][0]
        nlp = es_core_news_sm.load()
        doc = nlp(text)

        features = []
        for token in doc:
            features.append({'token' : token.text, 'pos' : token.pos_})

        fdf = pd.DataFrame(features)
        fdf.head(len(fdf))

        # Llamada para sacar el nombre del candidato
        if selector == 0:
            new_columns = ['Nombre','Apellido1', 'Apellido2']
            for n,col in enumerate(new_columns):
                df[col] = df['text'].apply(lambda x: encontrar_nombre(x, df)).apply(lambda x: x[n])
            print("El nombre completo del candidato es:", devolver_nombre(df))

        # Llamada para sacar el correo del candidato
        if selector == 1:
            data = open(fichero,'r')
            texto = data.read()

            r = re.compile(r'(\b[\w.]+@+[\w.]+.+[\w.]\b)')
            results = r.findall(texto)
            try:
                email_del_candidato = results[0]
                print("El email del candidato es:", email_del_candidato)
            except Exception as e:
                print('No hemos encontrado email')

        # Llamada para sacar el número de teléfono del candidato
        # Te dejo la estructura del email porque podría sacarse de forma similar
        if selector == 2:
            data = open(fichero,'r')
            texto = data.read()
            "[ (\[]{,1}[+]{,1}[ (\[]{,1}\d{0,4}[ )\]]{,1}[- ]{,3}\d{2,4}[- ]{,3}\d{2,4}[- ]{,3}\d{2,4}[- ]{,3}\d{0,4}"
            r = re.compile(r'[ (\[]{,1}[+]{,1}[ (\[]{,1}\d{0,4}[ )\]]{,1}[- ]{,3}\d{2,4}[- ]{,3}\d{2,4}[- ]{,3}\d{2,4}[- ]{,3}\d{0,4}')
            results = r.findall(texto)
            try:
                telefono_del_candidato = results[0]
                i = 0
                while(len(telefono_del_candidato.replace(" ", "").replace("-", "")) < 9):
                    i += 1
                    telefono_del_candidato = results[i]

                print("El teléfono del candidato es:", telefono_del_candidato)

            except Exception as e:
                print('No hemos encontrado teléfono de contacto')




        # Llamada a sacar los lenguajes de programación que conoce el candidato
        if selector == 3:
            print('Los lenguajes de programación que maneja el candidato son:', encontrar_lenguajes(df) + '.')

        # Llamada para sacar los idiomas que sabe el candidato
        if selector == 4:
            print("Los idiomas que maneja el candidato son:", encontrar_idiomas(df))

        # Llamada para sacar las referencias del candidato
        if selector == 5:
            print("Las referencias del candidato son:", encontrar_seccion(secciones[5],df))

        # Llamada para sacar la información académica del candidato
        if selector == 6:
            print("La formación académica del candidato es:", encontrar_seccion(secciones[1],df))

        # Llamada para sacar la información académica del candidato
        if selector == 7:
            print("La experiencia laboral del candidato es:", encontrar_seccion(secciones[0],df))

main()
