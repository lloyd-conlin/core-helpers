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

def getTreeInformation(srcFile):
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
    parentClassRef = mainClass.extends
    if parentClassRef is not None:
        parentClass = parentClassRef.name

    return mainClassName, parentClass, varNames

def generateMessages(srcFile):
    annotations = ["id"]
    messages = []

    mainClassName, parentClass, varNames = getTreeInformation(srcFile)

    if parentClass == "FoundationConfigurableContent":
        annotations.extend(["config", "configHandle", "localConfig", "localConfig.*"])

    messages.append(f"{mainClassName} = {formatVarName(mainClassName)}")
    if parentClass == "GenericContent" or "FoundationConfigurableContent":
        messages.append(f"models.content.{mainClassName} = {formatVarName(mainClassName)}")
    if parentClass == "FoundationConfigurableContent":
        messages.append(f"{mainClassName}.configHandle = Style")

    annotations.extend(varNames)
    for var in varNames:
        #print(var)
        splitName = string.capwords(re.sub(r"([A-Z])", r" \1", var))
        #print(splitName)
        messages.append(f"{mainClassName}.{var} = {splitName}")

    print(messages)
    print(annotations)

    global messagesString
    messagesString = f"# ----------------------- {mainClassName} -----------------------\n"
    for message in messages:
        messagesString += message + '\n'

    global annotationString

    annotationIncludeString = ""
    annotationEditString = ""
    styleTabAdded = False
    contentTabAdded = False

    for annotation in annotations:
        if not styleTabAdded and annotation == "config":
            annotationEditString += "\"tab:Style\","
            styleTabAdded = True
        annotationIncludeString += "\"" + annotation + "\","
        annotationEditString += "\"" + annotation + "\","
        if not contentTabAdded and annotation == "localConfig.*":
            annotationEditString += "\"tab:Content\","
            contentTabAdded = True

    annotationIncludeString = annotationIncludeString[:-1]
    annotationString = f"""@KRUDFields(edit={{{annotationEditString}}},
        include={{{annotationIncludeString}}})
    """

    global setupParamsString
    setupParamsString = ""
    if parentClass == "FoundationConfigurableContent":
        setupParamsString += "super.setupParams(params);\n"
    for var in varNames:
        setupParamsString += f'params.set("{var}", {var});\n'

    return True


def chooseFile(fileNameTextBox):
    src = filedialog.askopenfile(parent=window, mode='rb', title='Choose File')
    fileName = src.name
    print(fileName)
    fileNameTextBox.delete("1.0", tk.END)
    fileNameTextBox.insert(tk.END, fileName)
    return True


def changeDisplay(content):
    if content == "messages":
        label.config(text="Messages")
        print(messagesString)
        if messagesString != "":
            text.delete("1.0", tk.END)
            text.insert(tk.END, messagesString)
    elif content == "annotations":
        label.config(text="Annotations")
        print(annotationString)
        if annotationString != "":
            text.delete("1.0", tk.END)
            text.insert(tk.END, annotationString)
    elif content == "params":
        label.config(text="setupParams Body")
        print(setupParamsString)
        if setupParamsString != "":
            text.delete("1.0", tk.END)
            text.insert(tk.END, setupParamsString)


window = tk.Tk()
window.geometry("700x700")
window.maxsize(700, 700)

window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=1)
window.columnconfigure(2, weight=1)
window.columnconfigure(3, weight=1)
window.columnconfigure(4, weight=1)

labelFN = tk.Label(text="File Name")
labelFN.grid(row=0, column=2, pady=8)

fileNameText = tk.Text(window, state='normal', width=100, height=2)
fileNameText.grid(row=1, column=0, columnspan=5, padx=4)

buttonFN = tk.Button(window, text="Choose File", command=lambda: chooseFile(fileNameText))
buttonFN.grid(row=2, column=2, pady=8)

label = tk.Label(text="Messages")
label.grid(row=3, column=2, pady=8)

text = tk.Text(window, state='normal', width=100, height=20)
scroll = tk.Scrollbar(window)
text.configure(yscrollcommand=scroll.set)
text.grid(row=4, column=0, columnspan=5, padx=4)

buttonM = tk.Button(window, text="Generate Messages", command=lambda: generateMessages(fileNameText.get("1.0", tk.END)[:-1]))
buttonM.grid(row=5, column=2, pady=8)

buttonM1 = tk.Button(window, text="Display Messages", command=lambda: changeDisplay("messages"))
buttonM1.grid(row=6, column=1, pady=8)

buttonM2 = tk.Button(window, text="Display Annotations", command=lambda: changeDisplay("annotations"))
buttonM2.grid(row=6, column=2, pady=8)

buttonM3 = tk.Button(window, text="Display setupParams", command=lambda: changeDisplay("params"))
buttonM3.grid(row=6, column=3, pady=8)

window.mainloop()
