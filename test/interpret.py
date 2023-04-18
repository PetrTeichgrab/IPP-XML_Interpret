import re
import xml.etree.ElementTree as et
import argparse 

# author: Teichgráb Petr

#Definování listů obsahujících jednotlivé instrukce
FrameInstructions = ["move", "createframe", "popframe", "defvar", "pushframe"]
ArithmeticInstructions = ["add", "sub", "mul", "idiv"]
InputOutputTypeInstructions = ["write", "read", "type"]
LogicalInstructions = ["and", "or", "not", "lt", "gt", "eq"]
TypeConverterInstructions = ["int2char", "stri2int"]
StringInstructions = ["concat" , "strlen", "getchar", "setchar"]
DataFlowInstructions = ["jump", "jumpifeq", "jumpifneq", "exit", "label"]
CallReturnInstructions = ["call", "return"]
DebuggingInstructions = ["dprint", "break"]
NoneArgInstructions = ["createframe", "pushframe", "popframe", "return", "break"]
OneArgInstructions = ["defvar", "call", "write", "label", "jump", "exit", "dprint"]
TwoArgsInstructions = ["move", "int2char", "read", "strlen", "type", "not"]
ThreeArgsInstructions = ["add", "sub", "mul", "idiv", "and", "or", "lt", "gt", "eq", 
                         "concat", "getchar", "setchar", "jumpifeq", "jumpifneq", "stri2int"], 

Instructions = ["move", "createframe", "popframe", "defvar", "pushframe", "add", "sub", "mul", 
                "idiv", "write", "read", "type", "and", "or", "not", "lt", "gt", "eq", "int2char", 
                "stri2int", "concat" , "strlen", "getchar", "setchar", 
                "label","jump", "jumpifeq", "jumpifneq", "exit", "call", "return", "dprint", "break"]

#Slovník exit kódů
exitCodes = {
    "falseXMLformat" : 31,
    "unexpectedXMLstructure" : 32,
    "SemanticCheckError" : 52,
    "FalseOperandTypeError" : 53,
    "NonExistingVariableError" : 54,
    "NonExistingFrameError" : 55,
    "MissingValueError" : 56,
    "FalseOperandValueError" : 57,
    "FalseStringOperationError" : 58
}

#Třída ArgsParser starající se o načítání argumentů ze vstupu
class ArgsParser:
    #inicializace
    def __init__(self) -> None:
        self._sourceFile = ""
        self._inputFile = False
        self._inputFileLine = -1
        self._inputFileList = []

    #vytvoření parseru, použití třídy ArgumentParser
    def CreateParser(self):
        self.parser = argparse.ArgumentParser(
        prog='Interpret',
        description='Interpret XML kódu')
        return self.parser

    #Přidání jednotlivých argumentů do parseru
    def AddArgs(self):
        self.parser.add_argument('-s', '--source', nargs=1, 
                                 help="Argument source musí obsahovat cestu k souboru se XML reprezentací zdrojového kódu")
        self.parser.add_argument('-i', '--input', nargs=1, 
                                 help="Argument Input musí obsahovat cestu k souboru se vstupy pro samotnou interpretaci zadaného zdrojového kódu.")


    #Gettery, funkce pro přístup k 'privátním' atributum
    def GetSourceFile(self):
        return self._sourceFile

    def GetInputFileList(self):
        return self._inputFileList
    
    #Pří každém zavolání funkce se inkrementuje hodnota, která 
    # 'ukazuje' na aktuálně načítanou hodnotu z inputFile
    def GetInputFileLine(self):
        self._inputFileLine+=1
        return self._inputFileLine
    
    #Funkce převede xml kód ze vstupu na strom
    def GetXmlTree(self):
        return et.parse(self._sourceFile)

    #Zpracování argumentů a vytvoření listu z inputFile instrukcí
    def ProcessArgs(self):
        self.parser = self.CreateParser()
        self.AddArgs()
        arguments = self.parser.parse_args()
        if arguments.source:
            self._sourceFile = arguments.source[0]
        if arguments.input:
            self._inputFile = arguments.input[0]
            file = open(self._inputFile, 'r')
            inputListWithWS = file.readlines()

            #odstranění whitespace charakterů a přidání hodnot do listu
            for line in inputListWithWS:
                self._inputFileList.append(line.rstrip())

#Třída reprezentuje instrukci jazyka IPPcode23
class Instruction:

    #inicializace
    def __init__(self, order:int, opcode:str, frame):
        self._order = order
        self._opcode = opcode
        self._argList = []
        self._frame = frame
        self._typeControl = TypeController(frame)
    
    #Přidání argumentů instrukce
    def AddArgument(self,arg):
        self._argList.append(arg)

    #Gettery pro přístup k privátním atributum
    def GetOrder(self):
        return self._order
    
    def GetOpcode(self):
        return self._opcode
    
    def GetArgList(self):
        return self._argList
    
    #Funkce pro převedení charakterů reprezentovaných tříčíselným kódem na jejich hodnotu
    #Vstupem je řetězec načtený z funkce Read nebo ze zdrojového souboru
    #Výstupem je řetěze, který již neobsahuje charaktery v podobě kódů
    def ConvertString(self, EntryString):
        resultString = ''
        i = 0
        while i < len(EntryString):
            if i+3 < len(EntryString) and EntryString[i] == '\\' and EntryString[i+1:i+4].isdigit():
                resultString += chr(int(EntryString[i+1:i+4]))
                i += 4
            else:
                resultString += EntryString[i]
                i += 1
        return resultString
    
    #Funkce pro provedení instrukce
    def Execute(self):
            if self._opcode.lower() in Instructions:
                eval("self." + self._opcode.capitalize() + "()") 

    #Funkce vrací bool hodnotu na základě toho, zda je dané návěští již definováno
    def IsLabelDefined(self, labelDict, labelName):
        return labelName in labelDict
        
#Třída reprezentuje globální rámec a lokální a dočasné rámce
class Frame:
    #inicializace
    def __init__(self) -> None:
        self.globalFrame = []
        self.frameStack = []
        self.tempFrame = None

    #Přidání proměnné do rámce
    def Add(self, variable):

        #Podmínky pro ověření existence rámců
        if variable.GetFrame() == "TF" and self.tempFrame == None:
            exit(exitCodes["NonExistingFrameError"])
        if variable.GetFrame() == "LF" and self.frameStack == []:
            exit(exitCodes["NonExistingFrameError"])

        #Přidání proměnné do příslušného rámce
        if variable.GetFrame() == "GF":
            self.globalFrame.append(variable)
        if variable.GetFrame() == "TF":
            self.tempFrame.append(variable)
        if variable.GetFrame() == "LF":
            self.frameStack[-1].append(variable)
    
    #Odstraněnní příslušné proměnné z rámce
    def Remove(self, variable):
        if variable.GetFrame() == "GF":
            self.globalFrame.remove(variable)
        if variable.GetFrame() == "TF":
            self.tempFrame.remove(variable)
        if variable.GetFrame() == "LF":
            self.frameStack[-1].remove(variable)

    #Funkce zjišťuje zda-li je proměnná v daném rámci již definovaná
    def IsAlreadyDefined(self, variable):
        #Podmínky pro ověření existence rámců
        if variable.GetFrame() == "TF" and self.tempFrame == None:
            exit(exitCodes["NonExistingFrameError"])
        if variable.GetFrame() == "LF" and self.frameStack == []:
            exit(exitCodes["NonExistingFrameError"])

        if variable.GetFrame() == "GF":
            for v in self.globalFrame:
                if v.GetName() == variable.GetName():
                    exit(exitCodes["SemanticCheckError"])
        if variable.GetFrame() == "TF":
            for v in self.tempFrame:
                if v.GetName() == variable.GetName():
                    exit(exitCodes["SemanticCheckError"])
        if variable.GetFrame() == "LF":
            for v in self.frameStack[-1]:
                if v.GetName() == variable.GetName():
                    exit(exitCodes["SemanticCheckError"])

    #Funkce nalezne a vrátí proměnnou v příslušném rámci, není-li proměnná nalezena, funkce buď vrátí hodnotu
    #false nebo zrovna zavolá exit s příslušnou chybovou hláškou.
    def FindVariable(self, name, leave):
        try:
            frame, varName = name.split('@')
        except:
            return -1
        #Podmínky pro ověření existence rámců
        if frame == "TF" and self.tempFrame == None:
            exit(exitCodes["NonExistingFrameError"])
        if frame == "LF" and self.frameStack == []:
            exit(exitCodes["NonExistingFrameError"])

        #Hledání proměnné
        if frame == "GF":
            for v in self.globalFrame:
                if v.GetName() == varName:
                    return v
        elif frame == "TF":
            for v in self.tempFrame:
                if v.GetName() == varName:
                    return v
        elif frame == "LF":
            for v in self.frameStack[-1]:
                if v.GetName() == varName:
                    return v
                
        elif leave == True:
            exit(exitCodes["NonExistingVariableError"])
        else:
            return -2
        
    #Vytvoření dočasného rámce
    def CreateFrame(self):
        self.tempFrame = []

    #Pushnutí rámce
    def PushFrame(self):
        #Ověření existence dočasného rámce
        if self.tempFrame == None:
            exit(exitCodes["NonExistingFrameError"])
        for v in self.tempFrame:
            v.SetFrame("LF")

        self.frameStack.append(self.tempFrame)
        self.tempFrame = None
    
    #Popnutí rámce
    def PopFrame(self):
        #Ověření existence lokálního rámce
        if self.frameStack == []:
            exit(exitCodes["NonExistingFrameError"])
        for v in self.frameStack[-1]:
            v.SetFrame("TF")
        self.tempFrame = self.frameStack[-1]
        self.frameStack.remove(self.frameStack[-1])

#Třída reprezentující instrukci aritmetického typu. Třídá je potomek třídy Instruction
class ArithmeticInstruction(Instruction):

        #inicializace
        def __init__(self, order:int, opcode:str, frame):
            super().__init__(order, opcode, frame)

        #Metody reprezentující jednotlivé instrukce

        #Metoda představující instrukci add, která sečte dva operandy a uloží výsledek do proměnné
        def Add(self):
            var, operand1, operand2 = self.ProcessOperands()
            var.SetValue(operand1 + operand2)
        
        #Metoda představující instrukci sub, která odečte dva operandy a uloží výsledek do proměnné
        def Sub(self):
            var, operand1, operand2 = self.ProcessOperands()
            var.SetValue(operand1 - operand2)
        
        #Metoda představující instrukci add, která vynásobí dva operandy a uloží výsledek do proměnné
        def Mul(self):
            var, operand1, operand2 = self.ProcessOperands()
            var.SetValue(operand1 * operand2)
        
        #Metoda představující instrukci add, která vydělí dva operandy a uloží výsledek do proměnné
        def Idiv(self):
            var, operand1, operand2 = self.ProcessOperands()
            var.SetValue(operand1 - operand2)
            if(operand2 == 0):
                exit(exitCodes["FalseOperandValueError"])
            var.SetValue(int(operand1 // operand2))

        #Metoda zpracovává operandy a zajišťuje jejich typovou správnost a kompabilitu
        def ProcessOperands(self):
            arg1 = self._argList[0]
            var = self._frame.FindVariable(arg1.GetArgValue(), True)
            sym1 = self._argList[1]
            sym2 = self._argList[2]
            
            #Typová kontrola
            self._typeControl.CheckType(sym1,"int")
            self._typeControl.CheckType(sym2,"int")
            
            operand1 = int(sym1.GetSymbolValue(True))
            operand2 = int(sym2.GetSymbolValue(True))
            
            #Kontrola zda-li jsou proměnné inicializované
            if(operand1 == "NotInit" or operand2 == "NotInit"):
                exit(exitCodes["MissingValueError"])
            var.SetType("int")
            return var, operand1, operand2               

#Třída obsahující funkce, které reprezentují instrukce pracující s rámci
class FrameInstruction(Instruction):
        
        #inicializace
        def __init__(self, order:int, opcode:str, frame):
            super().__init__(order, opcode, frame)
            self._frame = frame
        
        #Metody reprezentující jednotlivé instrukce


        def Move(self):
            symbType = self._argList[1].GetDataType()
            symbVal = self._argList[1].GetSymbolValue(True)
            var = self._frame.FindVariable(self._argList[0].GetArgValue(), True)
            var.SetType(symbType)            
            var.SetValue(symbVal)

        def Defvar(self):
            arg = self._argList[0].GetArgValue()
            varFrame, varName = arg.split('@')
            #vytvoření proměnné a přidání do příslušného rámce
            var = Var(varName, varFrame)
            self._frame.IsAlreadyDefined(var)
            self._frame.Add(var)
        
        #Metody jsou implementovány ve třídě Frame
        def Createframe(self):
            self._frame.CreateFrame()

        def Pushframe(self):
            self._frame.PushFrame()

        def Popframe(self):
            self._frame.PopFrame()

#Třída reprezentující instrukce pro ladění programu
class DebuggingInstruction(Instruction):
        def __init__(self, order:int, opcode:str, frame):
            super().__init__(order, opcode, frame)
        def Execute(self):
            pass

#Třída reprezentuje instrukce pro načtení vstupu, vypsání hodnoty a zjištění typu
class InputOutputTypeInstruction(Instruction):

    #inicializace
    def __init__(self, order:int, opcode:str, frame):
        super().__init__(order, opcode, frame)

    #Metody reprezentující jednotlivé instrukce

    def Read(self, inputFile, line):
        type = self._argList[1].GetArgValue()
        var = self._frame.FindVariable(self._argList[0].GetArgValue(), True)
        
        #Zjištění zda-li se načte hodnota ze standartního vstupu nebo ze souboru
        if(inputFile != False):
            inputVal = inputFile[line]
        
        else:
            inputVal = input()
        

        result = None

        #Zjištění typu načteného vstupu a jeho následná konverze a přiřazení do výsledku
        if type == "int":
            if re.match(r'[-+]*[0-9]+$', inputVal):
                result = int(inputVal)
                var.SetType("int")

        elif type == "bool":
            #re.IGNORECASE zajišťuje, že nezáleží na velikosti písmen
            if re.match(r'^true$', inputVal, re.IGNORECASE):
                result = True
            else:
                result = False
            var.SetType("bool")

        elif type == "string":
            #Převedení číselných hodnot charakterů
            result = self.ConvertString(str(inputVal))
            var.SetType("string")

        #Zkontrolování proměnné
        self._typeControl.CheckType(self._argList[0], "var")

        #V případě chybného nebo chybějícího vstupu 
        #bude do proměnné ⟨var⟩ uložena hodnota nil@nil.
        if(result == None):
            var.SetType("nil")
            var.SetValue("nil")
        else:
            var.SetValue(result)


    #Funkce vypisuje hodnotu na standartní výstup
    def Write(self):
        output = self._argList[0]
        if output.GetDataType() == "nil":
            print("",end='')
        elif output.GetDataType() == "bool":
            print(str(output.GetSymbolValue(False)).lower(), end='')
        else:
            print(str(output.GetSymbolValue(False)), end = '')

    #Zjištění datového typu
    def Type(self):
        arg1 = self._argList[0]
        
        var = self._frame.FindVariable(arg1.GetArgValue(), True)

        symb = self._argList[1]

        symbType = symb.GetDataType()
        
        #Zjištění zda-li je proměnná inicializovaná, pokud ne, je do výsledné proměnné
        #uložen prázdný řetězec
        if symbType == False:
            var.SetValue("")
        else:
            var.SetValue(symbType)
    
    #Overriding rodičovské metody, protože každý funkce obsahuje jiné argumenty a funkce
    #Execute již nemůže obsahovat stejnou implementaci
    def Execute(self, args):
        instructionName = self._opcode.lower() 
        if instructionName == "read":
            self.Read(args.GetInputFileList(), args.GetInputFileLine())
        if instructionName== "write":
            self.Write()
        if instructionName == "type":
            self.Type()

#Třída obsahuje funkce reprezentující relační a booleovské instrukce
class LogicalInstruction(Instruction):

    #inicializace
    def __init__(self, order:int, opcode:str, frame):
            super().__init__(order, opcode, frame)

    #Metody reprezentující jednotlivé instrukce

    def Lt(self):
        var, operand1, operand2 = self.ProcessOperands()
        
        if operand1 < operand2:
            var.SetType("bool")
            var.SetValue(True)
        else:
            var.SetType("bool")
            var.SetValue(False)

    def Gt(self):
        var, operand1, operand2 = self.ProcessOperands()
        
        if operand1 > operand2:
            var.SetType("bool")
            var.SetValue(True)
        else:
            var.SetType("bool")
            var.SetValue(False)

    def Eq(self):
        arg1 = self._argList[1]
        arg2 = self._argList[2]
        self._typeControl.TypesEqualOrNil(arg1, arg2)

        var = self._frame.FindVariable(self._argList[0].GetArgValue(), True)
        operand1 = arg1.GetSymbolValue(True)
        operand2 = arg2.GetSymbolValue(True)

        if operand1 == operand2:
            var.SetType("bool")
            var.SetValue(True)
        else:
            var.SetType("bool")
            var.SetValue(False)

    def And(self):
        var, arg1, arg2 = self.ProcessLogicOperands()
        var.SetValue(arg1 and arg2)

    def Or(self):
        var, arg1, arg2 = self.ProcessLogicOperands()
        var.SetValue(arg1 or arg2)

    def Not(self):
        arg1 = self._argList[1]
        self._typeControl.CheckType(arg1, "bool")
        var = self._frame.FindVariable(self._argList[0].GetArgValue(), True)
        var.SetType("bool")
        arg1Val = arg1.GetSymbolValue(True)

        if arg1Val.lower() == "true":
            arg1Val = True
        else:
            arg1Val = False

        var.SetValue(not(arg1Val))

    #Funkce zpracovává operandy pro instrukce And a Or
    def ProcessLogicOperands(self):
        arg1 = self._argList[1]
        arg2 = self._argList[2]
        
        #typová kontrola
        self._typeControl.CheckType(arg1, "bool")
        self._typeControl.CheckType(arg2, "bool")
        var = self._frame.FindVariable(self._argList[0].GetArgValue(), True)
        var.SetType("bool")
        arg1Val = arg1.GetSymbolValue(True)
        arg2Val = arg2.GetSymbolValue(True)

        #konverze řetězcové hodnoty na skutečný bool typ
        if arg1Val.lower() == "true":
            arg1Val = True
        else:
            arg1Val = False

        if arg2Val.lower() == "true":
            arg2Val = True
        else:
            arg2Val = False

        return var, arg1Val, arg2Val
    
    #Funkce zpracovává operandy pro instrukce Lt a Gt
    def ProcessOperands(self):
        arg1 = self._argList[1]
        arg2 = self._argList[2]
        if(arg1.GetDataType() == "nil" or arg2.GetDataType() == "nil"):
            exit(exitCodes["FalseOperandTypeError"])

        self._typeControl.TypesEqual(arg1, arg2)
        var = self._frame.FindVariable(self._argList[0].GetArgValue(), True)

        return var, arg1.GetSymbolValue(True), arg2.GetSymbolValue(True)

#Třída reprezentuje instrukce pro konverzi mezi datovými typy
class TypeConversionInstruction(Instruction):

    #inicializace
    def __init__(self, order:int, opcode:str, frame):
        super().__init__(order, opcode, frame)

    #Metody reprezentující jednotlivé instrukce

    def Int2char(self):
        arg = self._argList[1]
        self._typeControl.CheckType(arg, "int")
        var = self._frame.FindVariable(self._argList[0].GetArgValue(), True)
        #Pokus o parsování int hodnoty
        try:
            char = chr(int(arg.GetSymbolValue(True)))
        except: 
            exit(exitCodes["FalseStringOperationError"])
        var.SetType("string")
        var.SetValue(char)
    
    def Stri2int(self):
        arg1 = self._argList[1]
        arg2 = self._argList[2]
        self._typeControl.CheckType(arg1, "string")
        self._typeControl.CheckType(arg2, "int")
        var = self._frame.FindVariable(self._argList[0].GetArgValue(), True)
        string = arg1.GetSymbolValue(True)
        stringLen = len(string)
        index = int(arg2.GetSymbolValue(True))

        #Kontrola rozsahu indexu 
        if index < 0 or index > (stringLen - 1):
            exit(exitCodes["FalseStringOperationError"])
        
        var.SetType("int")
        var.SetValue(ord(string[index]))

#Třída reprezentující intrukce pro operace se řetězci
class StringInstruction(Instruction):

    #inicializace
    def __init__(self, order:int, opcode:str, frame):
        super().__init__(order, opcode, frame)

    #Metody reprezentující jednotlivé instrukce

    def Concat(self):
        var, arg1, arg2 = self.ProcessInstruction()
        #kontrola typů
        self._typeControl.CheckType(arg1, "string")
        self._typeControl.CheckType(arg2, "string")

        var.SetType("string")
        var.SetValue(str(arg1.GetSymbolValue(True)) + str(arg2.GetSymbolValue(True)))

    def Strlen(self):
        arg = self._argList[1]
        var = self._frame.FindVariable(self._argList[0].GetArgValue(), True)

        #kontrola typů
        self._typeControl.CheckType(arg, "string")

        strLen = len(str(arg.GetSymbolValue(True)))
        var.SetType("int")
        var.SetValue(strLen)

    def Getchar(self):
        var, arg1, arg2 = self.ProcessInstruction()
        #kontrola typů
        self._typeControl.CheckType(arg1, "string")
        self._typeControl.CheckType(arg2, "int")

        string = str(arg1.GetSymbolValue(True))
        index = int(arg2.GetSymbolValue(True))

        #kontrola zda-li index není mimo hranice řetězce
        if index < 0 or index > (len(string)-1):
            exit(exitCodes["FalseStringOperationError"])

        var.SetType("string")
        var.SetValue(string[index])

    def Setchar(self):
        var, arg1, arg2 = self.ProcessInstruction()

        #kontrola typů
        self._typeControl.checkThreeArgs(self._argList[0], arg1, arg2, "string", "int", "string")

        modifiedString = str(var.GetValue())
        index = int(arg1.GetSymbolValue(True))
        stringToGetCharFrom = str(arg2.GetSymbolValue(True))

        #kontrola zda-li index není mimo hranice řetězce
        if index < 0 or index > (len(modifiedString)-1):
            exit(exitCodes["FalseStringOperationError"])
        
        #převedení stringu na list, a zpátky na string, protože 
        #python nepodporuje přiřazení při přistupu do řetězce za pomocí indexu
        modifiedStringList = list(modifiedString)
        modifiedStringList[index] = stringToGetCharFrom[0]
        modifiedString = ''.join(modifiedStringList)
        var.SetValue(modifiedString)

    #zpracování operandů pro instrukce
    def ProcessInstruction(self):
        arg1 = self._argList[1]
        arg2 = self._argList[2]
        var = self._frame.FindVariable(self._argList[0].GetArgValue(), True)
        return var, arg1, arg2

#Třída reprezentující intrukce pro řízení programu
class DataFlowInstruction(Instruction):

    #inicializace
    def __init__(self, order:int, opcode:str, frame):
        super().__init__(order, opcode, frame)

    #Metody reprezentující jednotlivé instrukce

    def Jump(self, labelDict, index):
        
        #Kontrola existence návěští        
        if not(self.IsLabelDefined(labelDict, self._argList[0].GetArgValue())):
            exit(exitCodes["SemanticCheckError"])
        
        index = int(labelDict[self._argList[0].GetArgValue()]) + 1
        return index

    def Jumpifeq(self, labelDict, index):

        #Kontrola existence návěští    
        if not(self.IsLabelDefined(labelDict, self._argList[0].GetArgValue())):
            exit(exitCodes["SemanticCheckError"])

        #Kontrola typů
        isEq = self._typeControl.TypesEqualOrNil(self._argList[1], self._argList[2], False)

        #Inkrementace indexu aby se mohlo pokračovat na další instrukci
        index = int(index)+1
        if not(isEq):
            return index

        if(self._argList[1].GetSymbolValue(True) != self._argList[2].GetSymbolValue(True)):
            return index
        
        index = int(labelDict[self._argList[0].GetArgValue()]) + 1
        return index

    def Jumpifneq(self, labelDict, index):

        #Kontrola existence návěští 
        if not(self.IsLabelDefined(labelDict, self._argList[0].GetArgValue())):
            exit(exitCodes["SemanticCheckError"])

        #Kontrola typů
        isEq = self._typeControl.TypesEqualOrNil(self._argList[1], self._argList[2], False)

        #Inkrementace indexu aby se mohlo pokračovat na další instrukci
        index = int(index)+1
        if not(isEq):
            return index

        if(self._argList[1].GetSymbolValue(True) == self._argList[2].GetSymbolValue(True)):
            return index
        
        index = int(labelDict[self._argList[0].GetArgValue()]) + 1
        return index

    def ExitProgram(self):
        arg = self._argList[0]

        #Typová kontrola
        self._typeControl.CheckType(arg, "int")
        exitVal = int(arg.GetSymbolValue(True))

        #Kontrola rozsahu exit kódů
        if exitVal not in range(0,50):
            exit(exitCodes["FalseOperandValueError"])
        exit(exitVal)

    def Execute(self, labelDict, index):
        if self._opcode.lower() in Instructions:
            if self._opcode.lower() == "exit":
                self.ExitProgram()
            method = getattr(self, self._opcode.capitalize())
            return method(labelDict, index)

#Třída reprezentující intrukce 'volání funkce' - skok na návěští s podporou návratu
class CallReturnInstruction(Instruction):

    #inicializace
    def __init__(self, order:int, opcode:str, frame):
        super().__init__(order, opcode, frame)

    #Metody reprezentující jednotlivé instrukce

    def Call(self, labelDict, callStack, index):

        #Kontrola existence návěští
        if not(self.IsLabelDefined(labelDict, self._argList[0].GetArgValue())):
            exit(exitCodes["SemanticCheckError"])
        callStack.append(index)
        index = int(labelDict[self._argList[0].GetArgValue()])+1
        return index, callStack

    def Return(self, labelDict, callStack, index):

        #Kontrola zda-li byla zavoláná funkce call
        if len(callStack) == 0:
            index+=1
            return index, callStack
        index = callStack[-1] + 1
        return index, callStack

    #Overriding rodičovské metody
    def Execute(self, labelDict, callStack, index):
        if self._opcode.lower() in Instructions:
            method = getattr(self, self._opcode.capitalize())
            return method(labelDict, callStack, index)
    
#Factory vracející příslušný typ instrukce
class InstructionFactory:

    #inicializace
    def __init__(self, order, opcode, frame) -> None:
        self._order = order
        self._opcode = opcode.lower()
        self._frame = frame

    def GetInstructionType(self):
        if self._opcode in FrameInstructions:
            return FrameInstruction(self._order, self._opcode, self._frame)
        if self._opcode in ArithmeticInstructions:
            return ArithmeticInstruction(self._order, self._opcode, self._frame)
        if self._opcode in InputOutputTypeInstructions:
            return InputOutputTypeInstruction(self._order, self._opcode, self._frame)
        if self._opcode in LogicalInstructions:
            return LogicalInstruction(self._order, self._opcode, self._frame)
        if self._opcode in TypeConverterInstructions:
            return TypeConversionInstruction(self._order, self._opcode, self._frame)
        if self._opcode in StringInstructions:
            return StringInstruction(self._order, self._opcode, self._frame)
        if self._opcode in DataFlowInstructions:
            return DataFlowInstruction(self._order, self._opcode, self._frame)
        if self._opcode in CallReturnInstructions:
            return CallReturnInstruction(self._order, self._opcode, self._frame)
        if self._opcode in DebuggingInstructions:
            return DebuggingInstruction(self._order, self._opcode, self._frame)

#Třída obsahující metody pro kontrolu typů
class TypeController:

    #inicializace
    def __init__(self, frame) -> None:
        self._frame = frame

    def checkThreeArgs(self, arg1, arg2, arg3, expectedType1, expectedType2, expectedType3):
        self.CheckType(arg1, expectedType1)
        self.CheckType(arg2, expectedType2)
        self.CheckType(arg3, expectedType3)
        
    def CheckType(self, arg, expectedSymbType):

        if expectedSymbType == "var": 
            self._frame.FindVariable(arg.GetArgValue(), True)

        if expectedSymbType == "int":
            if not(arg.IsIntConst()):
                if not(self.CheckVarsType(arg, "intVar")):
                    exit(exitCodes["FalseOperandTypeError"])

        if expectedSymbType == "string":
            if not(arg.IsIntConst()):
                if not(self.CheckVarsType(arg, "stringVar")):
                    exit(exitCodes["FalseOperandTypeError"])

        if expectedSymbType == "bool":
            if not(arg.IsBoolConst()):
                if not(self.CheckVarsType(arg, "boolVar")):
                    exit(exitCodes["FalseOperandTypeError"])

    def TypesEqual(self, arg1, arg2):
        if arg1.GetDataType() != arg2.GetDataType():
            exit(exitCodes["FalseOperandTypeError"])

    def TypesEqualOrNil(self, arg1, arg2, dontReturn):
        arg1Type = arg1.GetDataType()
        arg2Type = arg2.GetDataType()
        isNotEq = arg1Type != arg2Type and (arg1Type != "nil" or arg2Type != "nil")
        if dontReturn:
            if isNotEq:
                exit(exitCodes["FalseOperandTypeError"])

        return not(isNotEq)
        


    def CheckVarsType(self, arg, expectedVarType):
        if expectedVarType == "intVar":
            var = self._frame.FindVariable(arg.GetArgValue(), False)
            if(var == -2 or var == -1):
                return False
            if var.GetValue() == "NotInit":
                exit(exitCodes["MissingValueError"])
            if var.GetType() != "int":
                exit(exitCodes["FalseOperandTypeError"])
            return True

        if expectedVarType == "stringVar":
            var = self._frame.FindVariable(arg.GetArgValue(), False)
            if(var == -2 or var == -1):
                return False
            if var.GetValue() == "NotInit":
                exit(exitCodes["MissingValueError"])
            if var.GetType() != "string":
                exit(exitCodes["FalseOperandTypeError"])
            return True

        if expectedVarType == "boolVar":
            var = self._frame.FindVariable(arg.GetArgValue(), False)
            if(var == -2 or var == -1):
                return False
            if var.GetValue() == "NotInit":
                exit(exitCodes["MissingValueError"])
            if var.GetType() != "bool":
                exit(exitCodes["FalseOperandTypeError"])
            return True
        
#Třída reprezentuje argumenty instrukce
class InstructionArguments:

    def __init__(self, type, value, frame) -> None:
        self._argType = type[0]
        self._argValue = value
        self._frame = frame

    #Gettery pro přístup k privátním atributum
    def GetArgType(self):
        return self._argType
    
    def GetArgValue(self):
        return self._argValue
    
    #Pomocné funkce pro určení typu
    def IsVariable(self):
        if self._argType == "var":
            return True
        return False
    
    def IsIntConst(self):
        if self._argType == "int":
            return True
        return False
    
    def IsStringConst(self):
        if self._argType == "string":
            return True
        return False
    
    def IsBoolConst(self):
        if self._argType == "bool":
            return True
        return False
    
    def IsNilConst(self):
        if self._argType == "nil":
            return True
        return False
    
    #Funkce vraci hodnotu symbolu
    def GetSymbolValue(self, exitWhenNotInit):
        if self.IsVariable():
            var = self._frame.FindVariable(self._argValue, False)
            if var != -2:
                if exitWhenNotInit:
                    if not(var.IsInit()):
                        exit(exitCodes["MissingValueError"])
                if var.GetType() == "int" and var.GetType() != "NotInit":
                    return int(var.GetValue())
                else: 
                    return var.GetValue()
            else:
                #pokud nebyla promenna nalezena - error
                exit(exitCodes["NonExistingVariableError"])
        if self.IsIntConst():
            return (self._argValue)
        if self.IsStringConst():
            return self.ConvertString(str(self._argValue))
        if self.IsBoolConst() or self.IsNilConst():
            return self._argValue

    #pomocna funkce  
    def GetVarName(self):
        if self.IsVariable():
            name = self._argValue.split('@')
            return name[1]
    
    #Navraceni datoveho typu, pokud neni promenna incializovana, vraci False
    def GetDataType(self):
        if self.IsIntConst():
            return "int"
        if self.IsStringConst():
            return "string"
        if self.IsNilConst():
            return "nil"
        if self.IsBoolConst():
            return "bool"
        if self.IsVariable():
            var = self._frame.FindVariable(self._argValue, True)
            type = var.GetType()
            if type == "NotInit":
                return False
            return type

    #Funkce pro převedení charakterů reprezentovaných tříčíselným kódem na jejich hodnotu
    #Vstupem je řetězec načtený z funkce Read nebo ze zdrojového souboru
    #Výstupem je řetěze, který již neobsahuje charaktery v podobě kódů
    def ConvertString(self, EntryString):
        resultString = ''
        i = 0
        while i < len(EntryString):
            if i+3 < len(EntryString) and EntryString[i] == '\\' and EntryString[i+1:i+4].isdigit():
                resultString += chr(int(EntryString[i+1:i+4]))
                i += 4
            else:
                resultString += EntryString[i]
                i += 1
        return resultString
    
    #Zjisteni zda-li je promenna inicializovana, pokud ne - error
    def isVarInit(self):
        if self.IsVariable():
            var = self._frame.FindVariable(self._argValue, True)
            result = var.IsInit()
            if not(result):
                exit[exitCodes["MissingValueError"]]

#Třída reprezentující proměnnou
class Var:
    def __init__(self, name, frame) -> None:
        self._name = name
        self._frame = frame
        self._type = "NotInit"
        self._fullname = self._frame + "@" + self._name
        self._value = None

    #Gettery, pro pristup k privatnim atributum
    def GetName(self):
        return self._name
    
    def GetValue(self):
        return self._value
    
    def GetFullname(self):
        return self._fullname
    
    def GetFrame(self):
        return self._frame
    
    def GetType(self):
        return self._type
    
    #Settery, pro nastaveni hodnoty privatnich atributu
    def SetType(self, type):
        self._type = type

    def SetFrame(self, frame):
        self._frame = frame

    def SetName(self, name):
        self._name = name

    def SetValue(self, value):
        self._value = value

    def IsInit(self):
        if(self._value == None or self._type == "NotInit"):
            return False
        return True
    
#Třída pro řízení celého programu   
class Interpret:

    #inicializace
    def __init__(self) -> None:
        self._args = ArgsParser()
        self._tree = None
        self._root = None
        self._instructionList = []
    
    #Vytvoření XML stromu
    def makeXmlTree(self):
        self._args.ProcessArgs()
        self._tree = self._args.GetXmlTree()
        self._root = self._tree.getroot()

    def CheckRoot(self):
        programProps = list(self._root.attrib.values())
        if programProps[0] != "IPPcode23":
            exit(exitCodes["unexpectedXMLstructure"])
    #Průchod xml stromem a ukladani hodnot do listu instrukcí
    def ConvertXmlTreeToInstructList(self):

        #vytvoření framu pro předání do instrukcí
        self.CheckRoot()
        frame = Frame()
        orderList = []
        for ins in self._root:
            
            #kontrolola spravnosti tagu
            if not(re.match(r'instruction', ins.tag, re.IGNORECASE)):
                exit(exitCodes["unexpectedXMLstructure"])

            #list obsahujici order a opcode instrukce
            instructionProps = list(ins.attrib.values())
            
            #kontrola duplicitniho poradi instrukce
            if instructionProps[0] in orderList:
                exit(exitCodes["unexpectedXMLstructure"])

            if not(re.match(r'[0-9]', instructionProps[0], re.IGNORECASE)):
                exit(exitCodes["unexpectedXMLstructure"])

            if int(instructionProps[0]) == 0:
                exit(exitCodes["unexpectedXMLstructure"])

            #pridavani order do listu
            orderList.append(instructionProps[0])

                
            #vytvoření instrukce za pomocí factory
            instruction = InstructionFactory(int(instructionProps[0]), instructionProps[1], frame).GetInstructionType()
            
            #kontrola existence instrukce
            if instruction == None:
                exit(exitCodes["unexpectedXMLstructure"]) 

            argProps = []

            for arg in ins:

                #kontrolola spravnosti tagu
                if not(re.match(r'arg[0-9]', arg.tag, re.IGNORECASE)):
                    exit(exitCodes["unexpectedXMLstructure"])

                argProps.append(arg)

            #kontrola počtu argumentů dané instrukce

            if instruction.GetOpcode() in NoneArgInstructions:
                if len(argProps) != 0:
                    exit(exitCodes["unexpectedXMLstructure"])

            if instruction.GetOpcode() in OneArgInstructions:
                if len(argProps) != 1:
                    exit(exitCodes["unexpectedXMLstructure"])

            if instruction.GetOpcode() in TwoArgsInstructions:
                if len(argProps) != 2:
                    exit(exitCodes["unexpectedXMLstructure"])

            if instruction.GetOpcode() in ThreeArgsInstructions:
                if len(argProps) != 3:
                    exit(exitCodes["unexpectedXMLstructure"])

            #Seřazení argumentů do správného pořadí
            argProps.sort(key = lambda x: x.tag)

            #Přidání argumentů do instrukcí
            for arg in argProps:
                instructionArg = InstructionArguments(list(arg.attrib.values()), arg.text, frame)
                instruction.AddArgument(instructionArg)
            
            #Přidaní instrukce do listu
            self._instructionList.append(instruction)

        #Seřazení instrukcí podle order
        self._instructionList.sort(key=lambda x: x.GetOrder())

        #Koncová zarážka pro průchod cyklem
        self._instructionList.append("END")

    #Gettery, pro pristup k privatnim atributum
    def GetInstructionList(self):
        return self._instructionList
    
    def GetRoot(self):
        return self._root     

    def GetTree(self):
        return self._tree   
    
    #Funkce řídící celý program
    def Start(self):

        #Pokud je špatný vstup XML formátu - chyba 31
        try:
            self.makeXmlTree()
        except:
            exit(exitCodes["falseXMLformat"])

        self.ConvertXmlTreeToInstructList()
        #inicializace 
        index = 0
        labelDict = {}
        callStack = []
        
        #První průchod ve kterém se ukládají návěští do slovníku (vykonává pouze instrukci LABEL)
        while(self._instructionList[index] != "END"):
            if self._instructionList[index].GetOpcode().lower() == "label":
                argList = self._instructionList[index].GetArgList()
                if self._instructionList[index].IsLabelDefined(labelDict, argList[0].GetArgValue()):
                    exit(exitCodes["SemanticCheckError"])
                else:
                    labelDict[argList[0].GetArgValue()] = index

            index+=1

        index = 0

        #Druhý průchod, který již vykonává všechny instrukce (kromě instrukce LABEL)
        while(self._instructionList[index] != "END"):

            #Funkce Execute u instrukcí řídící tok programu vyžaduje jiné argumenty
            if self._instructionList[index].GetOpcode().lower() == "label":
                index+=1
                continue
            if self._instructionList[index].GetOpcode().lower() in DataFlowInstructions:
                index = self._instructionList[index].Execute(labelDict, index)
                continue
            if self._instructionList[index].GetOpcode().lower() in CallReturnInstructions:
                index, callStack = self._instructionList[index].Execute(labelDict, callStack, index)
                continue
            if self._instructionList[index].GetOpcode().lower() in InputOutputTypeInstructions:
                self._instructionList[index].Execute(self._args)
                index+=1
                continue

            self._instructionList[index].Execute()
            index+=1

#Program
i = Interpret()
i.Start()
