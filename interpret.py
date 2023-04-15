import re
import xml.etree.ElementTree as et
import argparse 

# author: Teichgráb Petr

# • 52 - chyba při sémantických kontrolách vstupního kódu v IPPcode23 (např. použití nedefino-
# vaného návěští, redefinice proměnné);
# • 53 - běhová chyba interpretace – špatné typy operandů;
# • 54 - běhová chyba interpretace – přístup k neexistující proměnné (rámec existuje);
# • 55 - běhová chyba interpretace – rámec neexistuje (např. čtení z prázdného zásobníku rámců);
# • 56 - běhová chyba interpretace – chybějící hodnota (v proměnné, na datovém zásobníku nebo
# v zásobníku volání);
# • 57 - běhová chyba interpretace – špatná hodnota operandu (např. dělení nulou, špatná návra-
# tová hodnota instrukce EXIT);
# • 58 - běhová chyba interpretace – chybná práce s řetězcem.
FrameInstructions = ["move", "createframe", "popframe", "defvar", "pushframe"]
ArithmeticInstructions = ["add", "sub", "mul", "idiv"]
InputOutputTypeInstructions = ["write", "read", "type"]
LogicalInstructions = ["and", "or", "not", "lt", "gt", "eq"]
Instructions = ["move", "createframe", "popframe", "defvar", "pushframe", "add", "sub", "mul", "idiv", "write", "read", "type", "and", "or", "not", "lt", "gt", "eq"]

exitCodes = {
    "SemanticCheckError" : 52,
    "FalseOperandTypeError" : 53,
    "NonExistingVariableError" : 54,
    "NonExistingFrameError" : 55,
    "MissingValueError" : 56,
    "FalseOperandValueError" : 57,
    "FalseStringOperationError" : 58
}


class ArgsParser:

    def CreateParser(self):
        self.parser = argparse.ArgumentParser(
        prog='Interpret',
        description='Interpret of XML code')
        return self.parser

    def AddArgs(self):
        self.parser.add_argument('-s', '--source', nargs=1)

    #TODO: def CheckArgs():

    def GetFileName(self):
        arguments = self.parser.parse_args()
        return arguments.source[0]
    
    def GetXmlTree(self):
        return et.parse(self.GetFileName())

    def ProcessArgs(self):
        self.parser = self.CreateParser()
        self.AddArgs()


class Instruction:

    def __init__(self, order:int, opcode:str, frame):
        self._order = order
        self._opcode = opcode
        self._argList = []
        self._frame = frame
        self._typeControl = TypeController(frame)
    
    def AddArgument(self,arg):
        self._argList.append(arg)

    def GetOrder(self):
        return self._order
    
    def GetOpcode(self):
        return self._opcode
    
    def GetArgs(self):
        return self._args
    
    def ConvertString(self, string):
        i = 0
        result = ''
        while i < len(string):
            if string[i] == '\\' and i+3 < len(string) and string[i+1:i+4].isdigit():
                # decode escaped sequence
                result += chr(int(string[i+1:i+4]))
                i += 4
            else:
                # append normal character
                result += string[i]
                i += 1
        return result
    
    def Execute(self):
            if self._opcode.lower() in Instructions:
                eval("self." + self._opcode.capitalize() + "()") 


class Frame:
    def __init__(self) -> None:
        self.globalFrame = []
        self.frameStack = []
        self.tempFrame = None
        self._globalVarsList = []
        self._localVarsList = []
        self._tempVarsList = []

    def Add(self, variable):
        if variable.GetFrame() == "GF":
            self.globalFrame.append(variable)
            self._globalVarsList.append(variable.GetName())
        if variable.GetFrame() == "TF":
            self.tempFrame.append(variable)
            self._tempVarsList.append(variable.GetName())
        if variable.GetFrame() == "LF":
            self.frameStack[-1].append(variable)
            self._localVarsList.append(variable.GetName())
    
    def Remove(self, variable):
        if variable.GetFrame() == "GF":
            self.globalFrame.remove(variable)
            self._globalVarsList.remove(variable.GetName())
        if variable.GetFrame() == "TF":
            self.tempFrame.remove(variable)
            self._tempVarsList.remove(variable.GetName())
        if variable.GetFrame() == "LF":
            self.frameStack[-1].remove(variable)
            self._localVarsList.remove(variable.GetName())

    def IsAlreadyDefined(self, variable):
        
        name = variable.GetName()
        if variable.GetFrame() == "GF" and name in self._globalVarsList:
            exit(exitCodes["SemanticCheckError"])
        if variable.GetFrame() == "TF" and name in self._tempVarsList:
            exit(exitCodes["SemanticCheckError"])
        if variable.GetFrame() == "LF" and name in self._localVarsList:
            exit(exitCodes["SemanticCheckError"])

    def FindVariable(self, name, leave):
        frame, varName = name.split('@')
        if frame == "GF" and varName in self._globalVarsList:
            for v in self.globalFrame:
                if v.GetName() == varName:
                    return v
        elif frame == "TF" and varName in self._tempVarsList:
            for v in self.tempFrame:
                if v.GetName() == varName:
                    return v
        elif frame == "LF" and varName in self._localVarsList:
            for v in self.frameStack[-1]:
                if v.GetName() == varName:
                    return v
        elif leave == True:
            exit(exitCodes["NonExistingVariableError"])
        else:
            return False
        
    def CreateFrame(self):
        self.tempFrame = []

    def PushFrame(self):
        for v in self.tempFrame:
            v.SetFrame("LF")
        self.frameStack.append(self.tempFrame)
        self._localVarsList.extend(self._tempVarsList)
        self.tempFrame = None
        self._tempVarsList = []
    
    def PopFrame(self):
        if bool(self._frameStackFrame):
            exit(exitCodes["NonExistingFrameError"])
        for v in self._frameStack[-1]:
            v.SetFrame("TF")
        self.tempFrame = self._frameStack[-1]
        self._tempVarsList.extend(self._localVarsList)
        self._localVarsList = []


class ArithmeticInstruction(Instruction):

        def __init__(self, order:int, opcode:str, frame):
            super().__init__(order, opcode, frame)

        def Add(self):
            var, operand1, operand2 = self.ProcessOperands()
            var.SetValue(operand1 + operand2)
        
        def Sub(self):
            var, operand1, operand2 = self.ProcessOperands()
            var.SetValue(operand1 - operand2)
        
        def Mul(self):
            var, operand1, operand2 = self.ProcessOperands()
            var.SetValue(operand1 * operand2)
        
        def Idiv(self):
            var, operand1, operand2 = self.ProcessOperands()
            var.SetValue(operand1 - operand2)
            if(operand2 == 0):
                exit(exitCodes["FalseOperandValueError"])
            var.SetValue(int(operand1 // operand2))

        def ProcessOperands(self):
            arg1 = self._argList[0]
            var = self._frame.FindVariable(arg1.GetArgValue(), True)
            sym1 = self._argList[1]
            sym2 = self._argList[2]
            if not((sym1.IsIntConst() or sym1.IsVariable()) and (sym2.IsIntConst or sym2.IsVariable())):
                exit(exitCodes["FalseOperandTypeError"])
            if (sym1.GetDataType() != "int" or sym2.GetDataType() != "int"):
                exit(exitCodes["FalseOperandTypeError"])

            operand1 = int(sym1.GetSymbolValue())
            operand2 = int(sym2.GetSymbolValue())
            if(operand1 == False or operand2 == False):
                exit(exitCodes["MissingValueError"])
            var.SetType("int")
            return var, operand1, operand2
        
        #overriding parent method
        def Execute(self):
            if self._opcode.lower() in ArithmeticInstructions:
                self._typeControl.checkThreeArgs(self._argList[0], self._argList[1], self._argList[2], "var", "int", "int")
                #calling appropriate function
                if self._opcode.lower() in ArithmeticInstructions:
                    eval("self." + self._opcode.capitalize() + "()")                  


class FrameInstruction(Instruction):
        def __init__(self, order:int, opcode:str, frame):
            super().__init__(order, opcode, frame)
            self._frame = frame

        def Move(self):
            symbType = self._argList[1].GetDataType()
            symbVal = self._argList[1].GetSymbolValue()
            var = self._frame.FindVariable(self._argList[0].GetArgValue(), True)
            var.SetType(symbType)            
            var.SetValue(symbVal)

        def Defvar(self):
            arg = self._argList[0].GetArgValue()
            varFrame, varName = arg.split('@')
            var = Var(varName, varFrame)
            self._frame.IsAlreadyDefined(var)
            self._frame.Add(var)
        
        def Createframe(self):
            self._frame.CreateFrame()

        def Pushframe(self):
            self._frame.PushFrame()

        def Popframe(self):
            self._frame.PopFrame()

        #overriding parent method


class InputOutputTypeInstruction(Instruction):
    def __init__(self, order:int, opcode:str, frame):
        super().__init__(order, opcode, frame)

    def Read(self):
        type = self._argList[1].GetArgValue()
        var = self._frame.FindVariable(self._argList[0].GetArgValue(), True)
        
        inputVal = input()
        result = None

        if type == "int":
            if re.match(r'[-+]*[0-9]+$', inputVal):
                result = int(inputVal)
                var.SetType("int")

        elif type == "bool":
            if re.match(r'^true$', inputVal, re.IGNORECASE):
                result = True
            else:
                result = False
            var.SetType("bool")

        elif type == "string":
            result = self.ConvertString(str(inputVal))
            var.SetType("string")

        self._typeControl.CheckType(self._argList[0], "var")

        var.SetValue(result)

        if(result == None):
            var.SetType("nil")

    def Write(self):
        output = self._argList[0]
        if output.GetDataType() == "nil":
            print("",end='')
        elif output.GetDataType() == "bool":
            print(str(output.GetSymbolValue()).lower(), end='')
        else:
            print(str(output.GetSymbolValue()), end = '')

    def Type(self):
        arg1 = self._argList[0]
        
        var = self._frame.FindVariable(arg1.GetArgValue(), True)

        symb = self._argList[1]

        symbType = symb.GetDataType()

        if symbType == "NotInit":
            var.SetValue("")
        else:
            var.SetValue(symbType)

    def Execute(self):
        if self._opcode.lower() in InputOutputTypeInstructions:
            eval("self." + self._opcode.capitalize() + "()") 


class LogicalInstruction(Instruction):
    def __init__(self, order:int, opcode:str, frame):
            super().__init__(order, opcode, frame)
            self._frame = frame

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
        self._typeControl.TypesEqual(arg1, arg2)

        var = self._frame.FindVariable(self._argList[0].GetArgValue(), True)
        operand1 = arg1.GetSymbolValue()
        operand2 = arg2.GetSymbolValue()

        if operand1 == operand2:
            var.SetType("bool")
            var.SetValue(True)
        else:
            var.SetType("bool")
            var.SetValue(False)

    def ProcessOperands(self):
        arg1 = self._argList[1]
        arg2 = self._argList[2]
        if(arg1.GetDataType() == "nil" or arg2.GetDataType() == "nil"):
            exit(exitCodes["FalseOperandTypeError"])

        self._typeControl.TypesEqual(arg1, arg2)
        var = self._frame.FindVariable(self._argList[0].GetArgValue(), True)

        return var, arg1.GetSymbolValue(), arg2.GetSymbolValue()

class InstructionFactory:
    
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
        

class TypeController:
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
            if not(arg.IsIntConst() or self.CheckVarsType(arg, "intVar")):
                exit(exitCodes["FalseOperandTypeError"])

        if expectedSymbType == "string":
            if not(arg.IsIntConst() or self.CheckVarsType(arg, "stringVar")):
                exit(exitCodes["FalseOperandTypeError"])

        if expectedSymbType == "bool":
            if not(arg.IsIntConst() or self.CheckVarsType(arg, "boolVar")):
                exit(exitCodes["FalseOperandTypeError"])

    def TypesEqual(self, arg1, arg2):
        if arg1.GetDataType() != arg2.GetDataType():
            exit(exitCodes["FalseOperandTypeError"])


    def CheckVarsType(self, arg, expectedVarType):
        if expectedVarType == "intVar":
            var = self._frame.FindVariable(arg.GetArgValue(), True)
            if var.GetType() != "int":
                exit(exitCodes["FalseOperandTypeError"])
            return True

        if expectedVarType == "stringVar":
            var = self._frame.FindVariable(arg.GetArgValue(), True)
            if var.GetType() != "string":
                exit(exitCodes["FalseOperandTypeError"])
            return True

        if expectedVarType == "boolVar":
            var = self._frame.FindVariable(arg.GetArgValue(), True)
            if var.GetType() != "bool":
                exit(exitCodes["FalseOperandTypeError"])
            return True
        

class InstructionArguments:

    def __init__(self, type, value, frame) -> None:
        self._argType = type
        self._argValue = value
        self._frame = frame

    def GetArgType(self):
        return self._argType[0]
    
    def GetArgValue(self):
        return self._argValue
    
    def IsVariable(self):
        if re.match(r'^(GF|LF|TF)@.*', self._argValue):   
            return True
        return False
    
    def IsIntConst(self):
        if re.match(r'^int@[-+]*[0-9]+$', self._argValue):
            return True
        return False
    
    def IsStringConst(self):
        if re.match(r'^string@.*', self._argValue):
            return True
        return False
    
    def IsBoolConst(self):
        if re.match(r'^bool@((true|false){1})$', self._argValue):
            return True
        return False
    
    def IsNilConst(self):
        if re.match(r'^nil@nil$|^nil@$', self._argValue):
            return True
        return False
    
    def GetSymbolValue(self):
        symbVal = self._argValue.split('@')
        var = self._frame.FindVariable(self._argValue, False)
        if var != False:
            if var.GetType() == "int":
                return int(var.GetValue())
            else: 
                return var.GetValue()
        if self.IsIntConst():
            return int(symbVal[1])
        if self.IsBoolConst() or self.IsStringConst() or self.IsNilConst():
            return symbVal[1]
        
    def GetVarName(self):
        if self.IsVariable():
            name = self._argValue.split('@')
            return name[1]
        
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
        

class Var:
    def __init__(self, name, frame) -> None:
        self._name = name
        self._frame = frame
        self._type = "NotInit"
        self._fullname = self._frame + "@" + self._name
        self._value = None

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
    
    def SetType(self, type):
        self._type = type

    def SetFrame(self, frame):
        self._frame = frame

    def SetName(self, name):
        self._name = name

    def SetValue(self, value):
        self._value = value

    def isInit(self):
        if(self._value == None):
            return False
        return True
    
     
class Interpret:
    def __init__(self) -> None:
        self._args = ArgsParser()
        self._tree = None
        self._root = None
        self._instructionList = []

    def makeXmlTree(self):
        self._args.ProcessArgs()
        self._tree = self._args.GetXmlTree()
        self._root = self._tree.getroot()

    def ConvertXmlTreeToInstructList(self):
        frame = Frame()
        for ins in self._root:
            instructionProps = list(ins.attrib.values())
            instruction = InstructionFactory(int(instructionProps[0]), instructionProps[1], frame).GetInstructionType()

            for arg in ins:
                instructionArg = InstructionArguments(list(arg.attrib.values()), arg.text, frame)
                instruction.AddArgument(instructionArg)
            
            self._instructionList.append(instruction)

        self._instructionList.sort(key=lambda x: x.GetOrder())

    def GetInstructionList(self):
        return self._instructionList
    
    def GetRoot(self):
        return self._root     

    def GetTree(self):
        return self._tree   
    
    def start(self):
        self.makeXmlTree()
        self.ConvertXmlTreeToInstructList()
        for instruction in self._instructionList:
            instruction.Execute()


i = Interpret()
i.start()







                

