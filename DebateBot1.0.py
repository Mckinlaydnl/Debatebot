import openai
import speech_recognition as speechRecogn
import pyttsx3
import json
import networkx as networkX
import plotly.graph_objects as graphObj

# Initialize the recognizer and TTS engine
recognizer = speechRecogn.Recognizer()
ttsEngine = pyttsx3.init()
openai.api_key = "API KEY REDACTED FOR SECURITY PURPOSES"

# Function to convert speech to text
def recognizeSpeech():
    with speechRecogn.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"User: {text}")
            return text
        except speechRecogn.UnknownValueError:
            print("Sorry, The program did not understand that.")
            return ""
        except speechRecogn.RequestError:
            print("Sorry, there was an error with the speech recognition service.")
            return ""

# Function to convert text to speech
def speak(text):
    ttsEngine.say(text)
    ttsEngine.runAndWait()
    

# Function to determine user intent using GPT-3.5
def determineIntent(text):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are being used for the purpose of a debate program where the user is using the program to improve their debating skills. Please determine the intent of the following statement and classify it as one of the four following categories. Is it a: Greeting, Goodbye, argument, or none? Please return the intent as solely one of these words and nothing else."},
            {"role": "user", "content": text}
        ]
    )
    intent = response.choices[0].message.content.strip()
    print(intent)
    return intent

#Function to parse GPT-3.5's response and seperate it into the three different catehrories
def parseArgumentResponse(response):
    parsedArgument = {}
    lines = response.split("\n")
    for line in lines:
        if line.startswith("Counterargument:"):
            parsedArgument['counterargument'] = line.replace("Counterargument: ", "").strip()
        elif line.startswith("Reason 1:"):
            parsedArgument['reason1'] = line.replace("Reason 1: ", "").strip()
        elif line.startswith("Evidence 1:"):
            parsedArgument['evidence1'] = line.replace("Evidence 1: ", "").strip()
        elif line.startswith("Reason 2:"):
            parsedArgument['reason2'] = line.replace("Reason 2: ", "").strip()
        elif line.startswith("Evidence 2:"):
            parsedArgument['evidence2'] = line.replace("Evidence 2: ", "").strip()
        elif line.startswith("Reason 3:"):
            parsedArgument['reason3'] = line.replace("Reason 3: ", "").strip()
        elif line.startswith("Evidence 3:"):
            parsedArgument['evidence3'] = line.replace("Evidence 3: ", "").strip()
    return parsedArgument

#Function to generate the initial argument
def generateArgument(debateHistory):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=debateHistory+[
            {"role": "system", "content": "You are being used for the purpose of a debate program where the user is using the program to improve their debating skills. Please generate an argument against the following statement. Provide the response in the following format:\nCounterargument: ...\nReason 1: ...\nEvidence 1: ...\nReason 2: ...\nEvidence 2: ...\nReason 3: ...\nEvidence 3: ..."},
        ]
    )

    argument = response.choices[0].message.content.strip()
    print(f"GPT-3.5 Response: {argument}")

    # Seperate the counterargument into the three different categories and save them
    parsedArgument = parseArgumentResponse(argument)
    return parsedArgument


#Function to continue argument
def continueArgument(debateHistory):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=debateHistory+[
            {"role": "system", "content": "You are being used for the purpose of a debate program where the user is using the program to improve their debating skills. Continue the argument based on the previous discussion, building upon your earlier counterarguments. Provide the response in the following format:\nCounterargument: ...\nReason 1: ...\nEvidence 1: ...\nReason 2: ...\nEvidence 2: ...\nReason 3: ...\nEvidence 3: ..."}
        ]
    )
    argument = response.choices[0].message.content.strip()
    print(f"GPT-3.5 Response: {argument}")

    # Parse the response into a dictionary
    parsed_argument = parseArgumentResponse(argument)
    return parsed_argument
    
  

#Function to genereate the argument map based on GPT-3.5s counterargument
def generateArgumentMap(counterArgument):
    G = networkX.DiGraph()
    
    # Main counterargument node
    G.add_node(0, label=counterArgument['counterargument'], role='counterargument', hover_text=counterArgument['counterargument'])
    
    reasons = ['reason1', 'reason2', 'reason3']
    evidence = ['evidence1', 'evidence2', 'evidence3']
    
    # Reasoning and Evidence nodes
    for i, reason in enumerate(reasons):
        if reason in counterArgument and counterArgument[reason]:
            reasonIndex = i + 1
            G.add_node(reasonIndex, label=counterArgument[reason], role='reason', hover_text=counterArgument[reason])
            G.add_edge(0, reasonIndex)
            
            evidenceKey = evidence[i]
            if evidenceKey in counterArgument and counterArgument[evidenceKey]:
                evidenceIndex = reasonIndex + 3  
                G.add_node(evidenceIndex, label=counterArgument[evidenceKey], role='evidence', hover_text=counterArgument[evidenceKey])
                G.add_edge(reasonIndex, evidenceIndex)
    
    # Node positioning
    pos = {}
    pos[0] = (0, 2)  # Main counterargument sits at the top

    # Positionings for the reason nodes
    for i, reason in enumerate(reasons):
        reasonIndex = i + 1
        pos[reasonIndex] = (i - 1, 1)  # Reasons in the middle layer

    # Poisitioning for the evidence nodes
    for i, reason in enumerate(reasons):
        reasonIndex = i + 1
        evidenceKey = evidence[i]
        if evidenceKey in counterArgument and counterArgument[evidenceKey]:
            evidenceIndex = reasonIndex + 3  
            pos[evidenceIndex] = (i - 1, 0)  # Puts the evidence nodes at the bottom

    # Create separate traces for node types
    edgeTrace = []
    nodeTrace = []
    middleEvidenceTrace = []

    # Add edge traces
    for edge in G.edges:
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edgeTrace.append(
            graphObj.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=2, color='blue'),
                showlegend=False,
                hoverinfo='none'
            )
        )
    
    # Add node traces
    for node in G.nodes:
        x, y = pos[node]
        nodeType = G.nodes[node]['role']
        text = G.nodes[node]['label']
        hover_text = G.nodes[node]['hover_text']
        
        if nodeType == 'evidence':
            # Separate trace for middle evidence nodes
            if node in [2, 5]:  
                middleEvidenceTrace.append(
                    graphObj.Scatter(
                        x=[x],
                        y=[y],
                        text=[text],
                        mode='markers+text',
                        textposition='bottom center',
                        hoverinfo='text',
                        marker=dict(
                            size=20,
                            color='yellow',
                            line=dict(width=2, color='black')
                        ),
                        textfont=dict(color='black')
                    )
                )
            else:
                nodeTrace.append(
                    graphObj.Scatter(
                        x=[x],
                        y=[y],
                        text=[text],
                        mode='markers+text',
                        textposition='top center',
                        hoverinfo='text',
                        marker=dict(
                            size=20,
                            color='yellow',
                            line=dict(width=2, color='black')
                        ),
                        textfont=dict(color='black')
                    )
                )
        else:
            nodeTrace.append(
                graphObj.Scatter(
                    x=[x],
                    y=[y],
                    text=[text],
                    mode='markers+text',
                    textposition='top center',
                    hoverinfo='text',
                    marker=dict(
                        size=20,
                        color='orange' if nodeType == 'reason' else 'red',
                        line=dict(width=2, color='black')
                    ),
                    textfont=dict(color='black')
                )
            )
    
    # Add a legend so users know what each node means
    legendTrace = graphObj.Scatter(
        x=[-1.5, -1.5, -1.5],
        y=[2, 1.5, 1],
        mode='markers',
        marker=dict(size=20, color=['red', 'orange', 'yellow']),
        text=['Counterargument', 'Reason', 'Evidence'],
        hoverinfo='text',
        textposition='middle right',
        showlegend=False
    )
    
    # Add annotations for the legend
    legendAnnotations = [
        dict(text='Counterargument', x=-1.5, y=2, xref='x', yref='y', showarrow=False, font=dict(color='black')),
        dict(text='Reason', x=-1.5, y=1.5, xref='x', yref='y', showarrow=False, font=dict(color='black')),
        dict(text='Evidence', x=-1.5, y=1, xref='x', yref='y', showarrow=False, font=dict(color='black'))
    ]
    
    fig = graphObj.Figure(data=[legendTrace] + nodeTrace + middleEvidenceTrace + edgeTrace)
    fig.update_layout(
        showlegend=False,
        title="Argument Map",
        annotations=legendAnnotations,
    )
    #Display the graph
    fig.show()

    
# Function to interact with the bot
def interactWithAI(intent, text, debateHistory):
    global counterArgument
    #Enter the users input into the debateHistory list
    debateHistory.append({"role": "user","content":text})

    #If the user is trying to greet the program, return a greeting back
    if intent == "Greeting":
        response = "Hello! How can I help you today?"
        debateHistory.append({"role": "assistant", "content": response})
        return response
    #If user is trying to say a goodbye, then return a goodbye
    elif intent == "Goodbye":
        response = "Goodbye! Have a great day!"
        debateHistory.append({"role": "assistant", "content": response})
        return response
    elif intent == "argument" or intent == "Argument":
        if len(debateHistory)==1: #If a counter arguement has not been generated or the debate has not started yet, generate the initial argument
            counterArgument = generateArgument(debateHistory)
            debateHistory.append({"role": "assistant", "content": counterArgument['counterargument']})
            speak(counterArgument['counterargument'])
            return counterArgument
        else:
            counterArgument = continueArgument(debateHistory)
            debateHistory.append({"role": "assistant", "content": counterArgument['counterargument']})
            speak(counterArgument['counterargument'])
            return counterArgument
    else:
        return f"I am not sure what you want me to say or do."

# Main 
def main():
    global debateHistory
    debateHistory = []
    
    print ("Welcome to DebateBot. This is a program that aims to allow the user to simulate a debate using AI.\n")
    userEnter = input("When you are ready, enter 1 and the program will begin listening to you.\n")
    while userEnter != "1":
        userEnter = input("That is not the correct input. Please enter 1\n")
    if userEnter == "1":
        while True:
            userInput = recognizeSpeech()
            if not userInput:
                continue
            intent = determineIntent(userInput)
            response = interactWithAI(intent, userInput, debateHistory)
            #If the user wants to say goodbye, say goodbye to them and close the program
            if intent == "Goodbye":
                speak(response)
                exit()
            if intent == "argument" or intent == "Argument":
                userEntry = input("\nYou have the option to generate an argument map for the AI's counterargument that shows you the main point it is making and its reasoning behind it. If you want to see the argument map, enter 1, otherwise press any other button.\n")
                if userEntry == "1":
                    generateArgumentMap(response)
                    userEntry = ""
                userEnter = input("To continue the debate, press 1. To end the program, enter any other button.\n")
                if userEnter != "1":
                    break
            else:
                speak(response)
            

# Start main on program start
main()
