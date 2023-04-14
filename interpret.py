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
    

class Frame:
    def __init__(self) -> None:
        self.globalFrame = []
        self.frameStack = []
        self.tempFrame = None
        self._globalVarsList = []
        self._localVarsList = []
        self._tempVarsList = []
        self.counter = 0

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

    def CreateFrame(self):
        self.tempFrame = []

    def PushFrame(self):
        self.frameStack.append(self.tempFrame)
        self._localVarsList.extend(self._tempVarsList)
        self.tempFrame = None
    
    def PopFrame(self):
        if bool(self._frameStackFrame):
            exit(exitCodes["NonExistingFrameError"])
        self.tempFrame = self._frameStack[-1]


class ArithmeticInstruction(Instruction):

        def __init__(self, order:int, opcode:str, frame):
            super().__init__(order, opcode, frame)

        def Add(var, sym1, sym2):
            var = sym1 + sym2
            return var
        
        def Sub(var, sym1, sym2):
            var = sym1 + sym2
            return var
        
        def Mul(var, sym1, sym2):
            var = sym1 * sym2
            return var
        
        def Idiv(var, sym1, sym2):
            if not((isinstance(var), int) and (isinstance(sym1,int) and isinstance(sym2), int)):
                exit(exitCodes["FalseOperandValueError"])
            if(sym2 == 0):
                exit(exitCodes["FalseOperandValueError"])
            var = sym1/sym2
            return var
        
        def Execute(self):
            if self._opcode.lower() in ArithmeticInstructions:
                TypeController.checkTypesThreeArgs(self._argList[0].GetArgType(), self._argList[1].GetArgType(), 
                                               self._argList[2].GetArgType(), "int", "int", "int")
                #calling appropriate function
                #eval(self._opcode.capitalize() + (self._argList[0], self._argList[1], self._argList[2]))                    


class FrameInstruction(Instruction):
        def __init__(self, order:int, opcode:str, frame):
            super().__init__(order, opcode, frame)
            self._frame = frame

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

        def Execute(self):
            if self._opcode.lower() in FrameInstructions:
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


class TypeController:
    def checkTypesThreeArgs(type1, type2, type3, expectedType1, expectedType2, expectedType3):
        if(type1 != expectedType1 or type2 != expectedType2 or type3 != expectedType3):
            exit(exitCodes["FalseOperandTypeError"])
    
        
class InstructionArguments:

    def __init__(self, type, value) -> None:
        self._argType = type
        self._argValue = value

    def GetArgType(self):
        return self._argType[0]
    
    def GetArgValue(self):
        return self._argValue


class Var:
    def __init__(self, name, frame) -> None:
        self._name = name
        self._frame = frame
        self._type = None

    def GetName(self):
        return self._name
    
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
                instructionArg = InstructionArguments(list(arg.attrib.values()), arg.text)
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







                

