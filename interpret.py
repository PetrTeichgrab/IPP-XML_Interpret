import re
import xml.etree.ElementTree as et
import argparse 

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
    
    def AddArgument(self,arg):
        self._argList.append(arg)

    def GetOrder(self):
        return self._order
    
    def GetOpcode(self):
        return self._opcode
    
    def GetArgs(self):
        return self._args
    
    def Execute(self):
            if self._opcode.lower() in FrameInstructions:
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
            exit(exitCodes["SemanticCheckError"])
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
            var.SetValue(operand1 // operand2)

        def ProcessOperands(self):
            arg1 = self._argList[0]
            var = self._frame.FindVariable(arg1.GetArgValue(), True)
            sym1 = self._argList[1]
            sym2 = self._argList[2]
            if not((sym1.IsIntConst() or sym1.IsVariable()) and (sym2.IsIntConst or sym2.IsVariable())):
                exit(exitCodes["FalseOperandTypeError"])

            operand1 = int(sym1.GetSymbolValue())
            operand2 = int(sym2.GetSymbolValue())
            return var, operand1, operand2
        
        #overriding parent method
        def Execute(self):
            if self._opcode.lower() in ArithmeticInstructions:
                TypeController.checkThreeArgsType(self._argList[0].GetArgType(), self._argList[1].GetArgType(), 
                                                  self._argList[2].GetArgType(), ["var"], ["int", "symb"],["int", "symb"])
                #calling appropriate function
                if self._opcode.lower() in ArithmeticInstructions:
                    eval("self." + self._opcode.capitalize() + "()")                  


class FrameInstruction(Instruction):
        def __init__(self, order:int, opcode:str, frame):
            super().__init__(order, opcode, frame)
            self._frame = frame

        def Move(self):
            pass

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
        def Execute(self):
            if self._opcode.lower() in FrameInstructions:
                eval("self." + self._opcode.capitalize() + "()") 


class InputOutputTypeInstruction(Instruction):
    def __init__(self, order:int, opcode:str, frame):
        super().__init__(order, opcode, frame)

    def Read(self):
        var = self._argList[0]
        type = self._argList[1] #string
        inp = input() #5

    def Type(self):
        arg1 = self._argList[0]
        
        var = self._frame.FindVariable(arg1.GetArgValue(), False)

        #TODO overwrite this method with implemented functions in InstructionArgument class

        if(var == False):
            exit(exitCodes["SemanticCheckError"])

        symb = self._argList[1]
        symbVal = symb.GetArgValue()

        #checking if symbol is variable
        if re.match(r'^(GF|LF|TF)@.*', symbVal):   
            
            varSymb = self._frame.FindVariable(symbVal, False)

            if (varSymb == False):
                exit(exitCodes["SemanticCheckError"])

            varType = varSymb.GetType()
            if varType == "NotInit":
                var.SetType("")     
            else:
                var.SetType(varSymb.GetType())

        else:
            if re.match(r'^int@[-+]*[0-9]+$', symbVal):
                var.SetType("int")
            if re.match(r'^string@.*', symbVal):
                var.SetType("string")
            if re.match(r'^bool@((true|false){1})$', symbVal):
                var.SetType("bool")
            if re.match(r'^nil@nil$|^nil@$', symbVal):
                var.SetType("nil")
            

    def Execute(self):
        if self._opcode.lower() in InputOutputTypeInstructions:
            eval("self." + self._opcode.capitalize() + "()") 


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
        

class TypeController:
    def checkType(type, expectedType):
        if not(type in expectedType):
            exit(exitCodes["FalseOperandTypeError"])   
    def checkThreeArgsType(type1, type2, type3, expectedType1, expectedType2, expectedType3):
        if not(type1 in expectedType1 and type2 in expectedType2 and type3 in expectedType3):
            exit(exitCodes["FalseOperandTypeError"])   
        
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
        val = self._argValue.split('@')
        if self.IsIntConst() or self.IsBoolConst() or self.IsStringConst() or self.IsNilConst():
            return val[1]
        if self.IsVariable():
            var = self._frame.FindVariable(val[1], True)
            return var.GetValue()
            

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







                

