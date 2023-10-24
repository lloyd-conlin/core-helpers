import javalang
import re
import string
import tkinter as tk
from tkinter import filedialog


def checkForAnnotation(annotationName, annotations):
    for annotation in annotations:
        if annotation.name == annotationName:
            return True
    return False

def formatVarName(varName):
    return string.capwords(re.sub(r"([A-Z])", r" \1", varName))

def getInformation(srcFile):
    with open(srcFile, "r") as file:
        data = file.read()
    file.close()
    # print(data)
    tree = javalang.parse.parse(data)
    varNames = []
    parentClass = ""
    print(tree)

    for _, node in tree.filter(javalang.tree.FieldDeclaration):
        print(node)
        for _, innerNode in node.filter(javalang.tree.VariableDeclarator):
            if not "final" in node.modifiers and not checkForAnnotation("Transient", node.annotations):
                varNames.append(innerNode.name)

    mainClass = list(tree.filter(javalang.tree.ClassDeclaration))[0][1]
    mainClassName = mainClass.name

    return mainClassName, parentClass, varNames

def generateMessages(srcFile):

    annotations = ["id"]
    messages = []

    mainClassName, parentClass, varNames= getInformation(srcFile)

    messages.append(f"{mainClassName} = {formatVarName(mainClassName)}")

    annotations.extend(varNames)
    for var in varNames:
        #print(var)
        splitName = string.capwords(re.sub(r"([A-Z])", r" \1", var))
        #print(splitName)
        messages.append(f"{mainClassName}.{var} = {splitName}")

    print(messages)
    print(annotations)

    messagesString = f"# ----------------------- {mainClassName} -----------------------\n"
    for message in messages:
        messagesString += message + '\n'

    text.delete("1.0", tk.END)
    text.insert(tk.END, messagesString)
    return True


def chooseFile(fileNameTextBox):
    src = filedialog.askopenfile(parent=window, mode='rb', title='Choose File')
    fileName = src.name
    print(fileName)
    fileNameTextBox.delete("1.0", tk.END)
    fileNameTextBox.insert(tk.END, fileName)
    return True


window = tk.Tk()
window.geometry("700x600")
labelFN = tk.Label(text="File Name")
labelFN.pack()

fileNameText = tk.Text(window, state='normal', width=100, height=2)
fileNameText.pack()

buttonFN = tk.Button(window, text="Choose File", command=lambda: chooseFile(fileNameText))
buttonFN.pack()

labelM = tk.Label(text="Messages")
labelM.pack()

text = tk.Text(window, state='normal', width=100, height=20)
scroll = tk.Scrollbar(window)
text.configure(yscrollcommand=scroll.set)
text.pack()

buttonM = tk.Button(window, text="Get Messages", command=lambda: generateMessages(fileNameText.get("1.0", tk.END)[:-1]))
buttonM.pack()

window.mainloop()
