import javalang
import re
import string
import tkinter as tk
from tkinter import filedialog


debug = False


def debugPrint(variable, variableName):
    """ Helper function to only print if the global 'debug' variable is set to True
    :param variable: variable to print out
    :type variable: Any
    :param variableName: heading to print above the variable to make it more distinguishable
    :type variableName: string
    :return: Nothing
    """
    debug and print(f"\n================ {variableName} ======================\n")
    debug and print(variable)


def checkForAnnotation(annotationName, annotations):
    """ Quick helper function to check if specified annotation is present
    :param annotationName: name of the annotation that is being looked for
    :type annotationName: string
    :param annotations: list of Annotation objects applied to the field in question
    :type annotations: list
    :rtype: bool
    :return: bool value determining presence of the annotation in question
    """
    for annotation in annotations:
        if annotation.name == annotationName:
            return True
    return False


def formatVarName(varName):
    """ Helper function to format the variable names, splitting on capital letters
    :param varName: string variable name as defined in the Java file
    :type varName: string
    :rtype: string
    :return: formatted string of varName, split into words based on capitalisation
    """
    return string.capwords(re.sub(r"([A-Z])", r" \1", varName))


def throwGUIError(errorKey, errorFieldVar):
    """ Error function to handle various errors that need to be thrown to the GUI
    :param errorKey: short key to determine type of error
    :type errorKey: string
    :param errorFieldVar: variable to set the error message to determine which field should show the error
    :type errorFieldVar: tk.StringVar
    :return: Nothing
    """
    if errorKey == 'no-file-chosen':
        errorFieldVar.set("No file has been selected - please choose a file before continuing")


def getTreeInformation(srcFile):
    """ Takes a path to a Java file and parses it to extract information on classes and variables that are defined
    :param srcFile: string path to Java file
    :type srcFile: string
    :rtype: (string, string, dict)
    :return: mainClassName, parentClass, varNames: strings for the main and parent class names, and a dict containing variable names and their associated types
    """
    if srcFile == '':
        return None
    with open(srcFile, "r") as file:
        data = file.read()
    file.close()
    debugPrint(data, "data")
    tree = javalang.parse.parse(data)
    varNames = {}
    parentClass = ""
    debugPrint(tree, "tree")

    mainClass = list(tree.filter(javalang.tree.ClassDeclaration))[0][1]
    mainClassName = mainClass.name
    varNames[mainClassName] = {}
    parentClassRef = mainClass.extends
    if parentClassRef is not None:
        parentClass = parentClassRef.name

    for _, node in tree.filter(javalang.tree.FieldDeclaration):
        debugPrint(node, "node")
        for _, innerNode in node.filter(javalang.tree.VariableDeclarator):
            # Transient and Final vars are deemed to be constants that don't need messages/annotations, so are ignored
            if not "final" in node.modifiers and not checkForAnnotation("Transient", node.annotations):
                varNames[mainClassName][innerNode.name] = node.type.name

    return mainClassName, parentClass, varNames


def generateAnnotations(treeInfo):
    """ Takes tuple of tree information to generate the edit and include entries for the KRUDDialog annotation
    :param treeInfo: tuple of tree information
    :type treeInfo: (string, string, dict)
    :rtype: string
    :return: annotationString: A string containing the complete KRUDDialog annotation with the include and edit sections filled in
    """
    mainClassName, parentClass, varNames = treeInfo
    annotations = ["id"]

    if parentClass == "FoundationConfigurableContent":
        annotations.extend(["config", "configHandle", "localConfig", "localConfig.*"])
    annotations.extend(varNames[mainClassName].keys())
    debugPrint(annotations, "annotations")

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

    return annotationString


def generateSetupParamsBody(treeInfo):
    """ Takes tuple of tree information to generate the body for the setupParams function
    :param treeInfo: tuple of tree information
    :type treeInfo: (string, string, dict)
    :rtype: string
    :return: setupParamsString: A string containing assignations of variables to the string of the var name for use in templates
    """
    mainClassName, parentClass, varNames = treeInfo
    setupParamsString = ""
    if parentClass == "FoundationConfigurableContent":
        setupParamsString += "super.setupParams(params);\n"
    for var in varNames[mainClassName].keys():
        setupParamsString += f'params.put("{var}", {var});\n'

    return setupParamsString


def generateConstructorBody(treeInfo):
    """ Takes tuple of tree information to generate the body for the base constructor function
    :param treeInfo: tuple of tree information
    :type treeInfo: (string, string, dict)
    :rtype: string
    :return: constructorString: A string containing default values set for each variable based on its type, for the base constructor function
    """
    mainClassName, parentClass, varNames = treeInfo
    constructorString = ""
    for var in varNames[mainClassName].keys():
        if varNames[mainClassName][var].lower() == "string":
            constructorString += f"this.{var} = \"\";\n"
        elif varNames[mainClassName][var].lower() == "list":
            constructorString += f"this.{var} = new ArrayList<>();\n"
        elif varNames[mainClassName][var].lower() == "boolean":
            constructorString += f"this.{var} = false;\n"
        else:
            constructorString += f"this.{var} = null;\n"

    return constructorString


def generateMessages(treeInfo):
    """ Takes tuple of tree information to generate the messages for the variables in the class
    :param treeInfo: tuple of tree information
    :type treeInfo: (string, string, dict[string, dict[string, string]])
    :rtype: string
    :return: messagesString: A string containing messages entries for all the variables provided, with \n chars at the end of each line
    """
    messages = []
    mainClassName, parentClass, varNames = treeInfo

    messages.append(f"{mainClassName} = {formatVarName(mainClassName)}")
    if parentClass == "GenericContent" or "FoundationConfigurableContent":
        messages.append(f"models.content.{mainClassName} = {formatVarName(mainClassName)}")
    if parentClass == "FoundationConfigurableContent":
        messages.append(f"{mainClassName}.configHandle = Style")

    for var in varNames[mainClassName].keys():
        splitName = formatVarName(var)
        messages.append(f"{mainClassName}.{var} = {splitName}")

    messagesString = f"# ----------------------- {mainClassName} -----------------------\n"
    for message in messages:
        messagesString += message + '\n'

    # Add a \n character to the end in case we concatenate the results of multiple of these calls
    return messagesString + '\n'


def processTree(srcFile, errorFields):
    """ Main processing function that parses the Java file and calls the generator functions with this info
    :param srcFile: path to the file to be parsed
    :type srcFile: string
    :param errorFields: dictionary of error field variables for error reporting
    :type errorFields: dict[string, tk.StringVar]
    :rtype: None
    :return: Nothing
    """
    treeInfo = getTreeInformation(srcFile)
    if treeInfo is None:
        throwGUIError("no-file-chosen", errorFields["file"])
        return None
    debugPrint(treeInfo[0], "mainClassName")
    debugPrint(treeInfo[1], "parentClass")
    debugPrint(treeInfo[2], "varNames")

    global content

    messagesString = generateMessages(treeInfo)
    content["messages"] = messagesString

    annotationString = generateAnnotations(treeInfo)
    content["annotations"] = annotationString

    setupParamsString = generateSetupParamsBody(treeInfo)
    content["params"] = setupParamsString

    constructorString = generateConstructorBody(treeInfo)
    content["constructor"] = constructorString


def chooseFile(fileNameTextBox):
    """ Function to get the file path to process
    :param fileNameTextBox: text entry box that holds the file path of the file to process
    :type fileNameTextBox: tk.Entry
    :rtype: bool
    :return: True
    """
    src = filedialog.askopenfile(parent=window, mode='rb', title='Choose File')
    fileName = src.name
    debugPrint(fileName, "fileName")
    fileNameTextBox.delete("1.0", tk.END)
    fileNameTextBox.insert(tk.END, fileName)
    return True


def changeDisplay(contentKey, content, labelString):
    """ Function to switch what is displayed in the text box, so that the user can copy the content to their files
    :param contentKey: which string should be displayed in the main text box
    :type contentKey: string
    :param content: collection of the strings that have been processed from the Java file
    :type content: dict[string, string]
    :param labelString: variable holding the title for the textbox
    :type labelString: tk.StringVar
    :rtype: None
    :return: Nothing
    """
    if contentKey == "messages":
        labelString.set("Messages")
        debugPrint(content[contentKey], "Messages")
    elif contentKey == "annotations":
        labelString.set("Annotations")
        debugPrint(content[contentKey], "Annotations")
    elif contentKey == "params":
        labelString.set("setupParams Body")
        debugPrint(content[contentKey], "setupParams Body")
    elif contentKey == "constructor":
        labelString.set("Constructor Body")
        debugPrint(content[contentKey], "Constructor Body")

    if content[contentKey] != "":
        text.delete("1.0", tk.END)
        text.insert(tk.END, content[contentKey])


if __name__ == '__main__':
    # Create the window object to hold the GUI
    window = tk.Tk()
    window.geometry("700x700")
    # window.maxsize(700, 700)

    # Configure columns for layout
    window.columnconfigure(0, weight=1)
    window.columnconfigure(1, weight=1)
    window.columnconfigure(2, weight=1)
    window.columnconfigure(3, weight=1)
    window.columnconfigure(4, weight=1)

    # Initialise label variables
    textbox_string = tk.StringVar()
    fileError_string = tk.StringVar()

    # Initialise global variables
    content = {
        "messages": "",
        "annotations": "",
        "params": "",
        "constructor": "",
    }

    # Dictionary to hold the error variables for error reporting
    errorFields = {
        "file": fileError_string
    }

    labelFileName = tk.Label(text="File Name")
    labelFileName.grid(row=0, column=2, pady=8)

    fileNameText = tk.Text(window, state='normal', width=100, height=2)
    fileNameText.grid(row=1, column=0, columnspan=5, padx=4)

    labelFileNameError = tk.Label(textvariable=fileError_string)
    labelFileNameError.grid(row=2, column=2, pady=8)

    # Wrapping the intended function in a lambda to pass to the command option
    # as the function supplied needs to take no arguments
    buttonChooseFile = tk.Button(window, text="Choose File", command=lambda: chooseFile(fileNameText))
    buttonChooseFile.grid(row=3, column=2, pady=8)

    labelTextBox = tk.Label(textvariable=textbox_string)
    labelTextBox.grid(row=4, column=2, pady=8)

    text = tk.Text(window, state='normal', width=100, height=20)
    scroll = tk.Scrollbar(window)
    text.configure(yscrollcommand=scroll.set)
    text.grid(row=5, column=0, columnspan=5, padx=4)

    # Removing last character from fileNameText string as it inserts a \n character automatically
    buttonProcessInfo = tk.Button(window, text="Generate Messages", command=lambda: processTree(fileNameText.get("1.0", tk.END)[:-1], errorFields))
    buttonProcessInfo.grid(row=6, column=2, pady=8)

    buttonShowMessages = tk.Button(window, text="Display Messages", command=lambda: changeDisplay("messages", content, textbox_string))
    buttonShowMessages.grid(row=7, column=1, pady=8)

    buttonShowAnnotations = tk.Button(window, text="Display Annotations", command=lambda: changeDisplay("annotations", content, textbox_string))
    buttonShowAnnotations.grid(row=7, column=2, pady=8)

    buttonShowSetupParams = tk.Button(window, text="Display setupParams", command=lambda: changeDisplay("params", content, textbox_string))
    buttonShowSetupParams.grid(row=7, column=3, pady=8)

    buttonShowConstructor = tk.Button(window, text="Display constructor", command=lambda: changeDisplay("constructor", content, textbox_string))
    buttonShowConstructor.grid(row=8, column=1, pady=8)

    window.mainloop()
