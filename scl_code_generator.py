import os
from dotenv import load_dotenv, find_dotenv
from zhipuai import ZhipuAI
from prompts import *
import json
import logging
import regex as re
from time import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
    )

def timer(func):
    def func_wrapper(*args, **kwargs):
        time_start = time()
        result = func(*args, **kwargs)
        time_end = time()
        time_spend = time_end - time_start
        logging.info('%s cost time: %.3f s' % (func.__name__, time_spend))
        return result
    return func_wrapper


class GLMCodeGenerator:
    """
    Base class for code generator using GLM model.
    """
    def __init__(self) -> None:
        self.zhipu_api_key = os.environ.get('ZHIPU_API_KEY')
        self.client = ZhipuAI(api_key=self.zhipu_api_key) #APIKey

    def get_model_response(self, query_prompt:str,  history_messages: list, model_name = "glm-4-0520", top_p = 0.7, temperature = 0.01):
        """
        Get response from the model.
        !! Will update history message at the same time.
        """
        history_messages.append({"role": "user", "content": query_prompt})

        response = self.client.chat.completions.create(
            model=model_name,
            messages=history_messages,
            top_p=top_p,
            temperature=temperature,
        )
        history_messages.append({"role": "assistant", "content": response.choices[0].message.content})
        return response.choices[0].message.content
    
    def extract_code_from_response(self, code: str):
        """
        用正则表达式，提取```scl和```之间的内容
        """
        pattern = re.compile(r'```scl(.*?)```', re.DOTALL)
        match = pattern.search(code)
        if match:
            code = match.group(1)
        else:
            logging.debug("No code found in response.")

        return code
    
    def save(self, code: str, file_path: str):
        with open(file_path, 'w', encoding='utf_8_sig') as file:
            file.write(code)
        logging.info("Code saved to %s", file_path)


class SCLLogicGenerator(GLMCodeGenerator):
    """
    用glm生成变量声明和逻辑，用以作为后续代码生成的参考
    """
    def __init__(self) -> None:
        _ = load_dotenv(find_dotenv("./.env"))
        self.zhipu_api_key = os.environ.get('ZHIPU_API_KEY')
        
        self.client = ZhipuAI(api_key=self.zhipu_api_key) #APIKey
        self.prompt = LogicPrompt()

        self.history = []
        system_prompt = self.prompt.get_init_prompt()
        self.history.append({"role": "system", "content": system_prompt})
    
    @timer
    def generate_logic(self, json_str):
        question = self.prompt.get_query_prompt(json_str)
        response = self.get_model_response(question, self.history, temperature=0.1)

        return response


class SCLCodeChecker(GLMCodeGenerator):
    """
    按照规则检查已有的scl代码，并生成新的scl代码
    包含以下子功能：
    × 1. 使用zhipu api检查代码 - 功能移至prompt实现，暂时屏蔽
    × 2. 给主程序代码中的变量添加# - 通过prompt和example实现，暂时屏蔽
    √ 3. 用规则检查代码
    """
    def __init__(self) -> None:
        self.zhipu_api_key = os.environ.get('ZHIPU_API_KEY')
        self.client = ZhipuAI(api_key=self.zhipu_api_key) #APIKey
        logging.info("SCLCodeChecker initialized.")
        
    @timer
    def check_with_zhipu(self, code:str):
        """
        使用zhipu api检查代码
        为单次调用、不带记忆的检查
        """
        history = []
        prompt = RefinePrompt()
    
        system_prompt = prompt.get_init_prompt()
        history.append({"role": "system", "content": system_prompt})

        query_prompt = prompt.get_query_prompt(code)

        response = self.get_model_response(query_prompt, history)
        response = self.extract_code_from_response(response)
        
        logging.debug("Code checked with model. New code: %s", response)
        return response
    
    def hash_tag_helper(self, json_data: json, code: str):
        """
        给主程序代码中的变量添加#
        为单词调用、不带记忆的API调用
        """
        # 1.将json数据中的变量名提取出来
        variables = set()
        for key in json_data.keys():
            if key in ["input", "output", "in/out"]:
                for value in json_data[key]:
                    # 当value和value['name']都存在时，读取value['name']
                    if isinstance(value, dict) and 'name' in value.keys():
                        variables.add(value['name'])
        
        # 2.给代码中的变量添加#
        prompt = HashTagHelperPrompt()
        query_prompt = prompt.get_query_prompt(code, variables)

        history = []

        response = self.get_model_response(query_prompt, history)
        response = self.extract_code_from_response(response)

        logging.debug("# Added. New code: %s", response)
        return response
    
    @timer
    def check_with_rule(self, code:str):
        """
        用规则检查代码
        """
        # 1.替换==为=
        code = code.replace("==", "=")
    
        # 2.如果某一行包含且仅包含"END"或者"END;"，去除这一行
        code = code.replace("END;\n", "")
        code = code.replace("END\n", "")

        # 3.假如结尾被错误添加了分号，则去除分号
        code = code.replace("END_FUNCTION_BLOCK;", "END_FUNCTION_BLOCK")
        code = code.replace("END_FUNCTION;", "END_FUNCTION")

        # 4.添加缺失的分号
        code = code.replace("END_IF\n", "END_IF;\n")
        code = code.replace("END_FOR\n", "END_FOR;\n")
        code = code.replace("END_STRUCT\n", "END_STRUCT;\n")
        code = code.replace("End_Struct\n", "End_Struct;\n")
        code = code.replace("END_CASE\n", "END_CASE;\n")

        # 5.处理经常输出错误的除号和counter问题
        code = code.replace(" DIV ", "/")
        code = code.replace("counter", "counter_rep")

        return code
        
        
    def check_code(self, json_data, code: str):
        # 功能挪至prompt实现，暂时屏蔽
        # code = self.check_with_zhipu(code)
        code = self.check_with_rule(code)
        return code

class SCLCodeGenerator(GLMCodeGenerator):
    """
    按要求生成scl代码
    """
    def __init__(self):
        _ = load_dotenv(find_dotenv("./.env"))
        self.zhipu_api_key = os.environ.get('ZHIPU_API_KEY')
        
        self.client = ZhipuAI(api_key=self.zhipu_api_key) #APIKey
        self.logic_generator = SCLLogicGenerator()
        self.logic = ""
        self.checker = SCLCodeChecker()
        self.prompt = CodeGeneratorPromptForFunctionBlock()

        self.history = []
        system_prompt = self.prompt.get_init_prompt()
        self.history.append({"role": "system", "content": system_prompt})
        logging.info("SCLCodeGenerator initialized.")
    
    def get_relavant_context(self, json_data: json):
        """
        获取赛题相关的上下文。
        当前版本为一个hard code的字符串。
        TODO: Get relevant context from knowledge base
        TODO: 加入其它系统API
        """
        return """
{
  "name": "SHR",
  "description": "使用“右移”指令，可以将参数 IN 的内容逐位向右移动，并将结果作为函数值返回。参数 N 用于指定应将特定值移位的位数。如果参数 N 的值为“0”，则将参数 IN 的值作为结果。如果参数 N 的值大于可用位数，则参数 IN 的值将向右移动该位数个位置。无符号值移位时，用零填充操作数左侧区域中空出的位。如果指定值有符号，则用符号位的信号状态填充空出的位。",
  "param": [
    {
      "name": "IN",
      "declaration": "Input",
      "data_type": "位字符串、整数",
      "storage_area": "I、Q、M、D、L",
      "description": "要移位的值"
    },
    {
      "name": "N",
      "declaration": "Input",
      "data_type": "USINT、UINT、UDINT",
      "storage_area": "I、Q、M、D、L",
      "description": "对值 (IN) 进行移位的位数"
    },
    {
      "name": "函数值",
      "declaration": "Output",
      "data_type": "位字符串、整数",
      "storage_area": "I、Q、M、D、L",
      "description": "指令的结果"
    }
  ],
  "example": {
    "scl_code": "\"Tag_Result\" := SHR(IN := \"Tag_Value\", N := \"Tag_Number\");"
  }
}


{
  "name": "INT_TO_REAL",
  "description": "把INT转为REAL",
  "example": {
    "scl_code": "\"Tag_REAL\" := INT_TO_REAL(\"Tag_INT\");"
  }
}

{
  "name": "ABS",
  "description": "计算绝对值",
  "example": {
    "scl_code": "\"Tag_Result1\" := ABS(\"Tag_Value\");\n\"Tag_Result2\" := ABS(\"Tag_Value1\"*\"Tag_Value2\");",
    "description": "输入值的绝对值作为函数值以输入值的格式返回。"
  }
}

{
  "name": "CEIL",
  "description": "使用“浮点数向上取整”指令将值取整为最近接的整数。该指令将输入值解释为浮点数，并将其转换为紧邻的较大整数。函数值可以大于或等于输入值。",
  "example": {
    "code": [
      "SCL",
      "\"Tag_Result1\" := CEIL(\"Tag_Value\");",
      "\"Tag_Result2\" := CEIL_REAL(\"Tag_Value\");"
    ],
    "values": {
      "Tag_Value": [0.5, -0.5],
      "Tag_Result1": [1, 0],
      "Tag_Result2": [1.0, 0.0]
    }
  }
}

{
  "name": "FLOOR",
  "description": "使用“浮点数向下取整”指令将一个浮点数的值取整为紧邻的较小整数。该指令将输入值解释为浮点数，并将其转换为紧邻的较小整数。函数值可等于或小于输入值。",
  "example": {
    "code": [
      "SCL",
      "\"Tag_Result1\" := FLOOR(\"Tag_Value\");",
      "\"Tag_Result2\" := FLOOR_REAL(\"Tag_Value\");"
    ],
    "values": {
      "Tag_Value": [0.5, -0.5],
      "Tag_Result1": [0, -1],
      "Tag_Result2": [0.0, -1.0]
    }
  }
}

{
  "name": "REF",
  "description": "Creates a reference to a variable using the 'REF()' keyword, where the parameter specifies the variable to be referenced.",
  "param": {
    "<expression>": {
      "declaration": "Input",
      "data_type": "Bit sequence (except BOOL), integer, floating-point number, string, PLC data type (UDT), system data type (SDT), ARRAY of named data type",
      "storage_location": "DB variable (optimized), FB block interface (optimized)",
      "description": "The variable to be referenced"
    },
    "Function value": {
      "data_type": "Depends on the declared reference variable",
      "storage_location": "FC block interface: Input, Output, Temp; FB block interface: Temp",
      "description": "Address of the referenced variable"
    }
  },
  "example": {
    "scl_code": "#myRefInt := REF(#a);\n#myRefType := REF(\"myDB\".myUDT);\n#myRefType := REF(\"myArrayDB_UDT\".\"THIS\"[1]);\n#myRefARRAY := REF(\"myDB\".myArray);",
    "description": "Declares temporary variables '#myRefInt', '#myRefType', and '#myRefArray' in the block interface and assigns corresponding variables in the program code."
  }
}

{
  "name": "NORM_X",
  "description": "The 'Normalization' instruction standardizes the value of the input variable VALUE by mapping it to a linear scale. The value range for the scale can be defined using the parameters MIN and MAX. The result in the output OUT is calculated and stored as a floating-point number, depending on the position of the value to be standardized in the value range. If the value to be standardized is equal to the input MIN, the instruction returns the result '0.0'. If the value to be standardized is equal to the input MAX, the instruction returns the result '1.0'.",
  "example": {
    "scl_code": "\"Tag_Result1\" := NORM_X(MIN := \"Tag_Value1\", VALUE := \"Tag_InputValue\", MAX := \"Tag_Value2\");\n\"Tag_Result2\" := NORM_X_LREAL(MIN := \"Tag_Value1\", VALUE := \"Tag_InputValue\", MAX := \"Tag_Value2\");",
    "explanation": "The instruction's result is returned as the function value in the 'Tag_Result' operand."
  }
}

{
  "name": "ROUND",
  "description": "取整指令用于将输入IN的值取整为最接近的整数。该指令将输入IN的值解释为浮点数，并将其转换为一个整数或浮点数。如果输入值恰好是在一个偶数和一个奇数之间，则选择偶数。",
  "example": {
    "scl_code": "\"Tag_Result\" := ROUND(\"Tag_Value\");",
    "description": "该指令的结果作为函数值在“Tag_Result”操作数中返回。"
  }
}

{
  "name": "TRUNC",
  "description": "“截尾取整”指令用于直接从输入值中截取整数。该指令仅选择输入值的整数部分，并将这一部分（不含小数位）作为函数值返回。",
  "example": {
    "scl_code": [
      "\"Tag_Result1\" := TRUNC(\"Tag_Value1\");",
      "\"Tag_Result2\" := TRUNC(\"Tag_Value2\"+\"Tag_Value3\");",
      "\"Tag_Result3\" := TRUNC_SINT(\"Tag_Value4\");"
    ]
  }
}
"""
    @timer
    def generate_code(self, json_data: json):
        json_str = json.dumps(json_data)
        # first step: generate logic
        self.logic = self.logic_generator.generate_logic(json_str)
        logging.debug("Logic generated: %s", self.logic)

        # second step: get code from AI model
        context = self.get_relavant_context(json_data)
        query_prompt = self.prompt.get_query_prompt(json_str, context, self.logic)
        response = self.get_model_response(query_prompt, self.history, temperature=0.01)
        logging.debug("Code generated: %s", response)

        # third step: refine the code
        response = self.extract_code_from_response(response)
        response = self.checker.check_code(json_data, response)
        logging.debug("Code checked: %s", response)

        return response


class SCLCodeGeneratorForFunction(SCLCodeGenerator):
    """
    对Function类型的题目进行代码生成
    """
    def __init__(self):
        _ = load_dotenv(find_dotenv("./.env"))
        self.zhipu_api_key = os.environ.get('ZHIPU_API_KEY')
        
        self.client = ZhipuAI(api_key=self.zhipu_api_key) #APIKey
        self.logic_generator = SCLLogicGenerator()
        self.logic = ""
        self.checker = SCLCodeChecker()
        self.prompt = CodeGeneratorPromptForFunction()

        self.history = []
        system_prompt = self.prompt.get_init_prompt()
        self.history.append({"role": "system", "content": system_prompt})
        logging.info("SCLCodeGenerator initialized.")


if __name__ == "__main__":
    def test_generate_one_answer(question_file_name:str, scl_file_name:str):
        scl_code_generator = SCLCodeGenerator()
        with open(question_file_name, 'r', encoding='utf_8_sig') as file:
            json_data = json.load(file)

        response = scl_code_generator.generate_code(json_data)
        scl_code_generator.save(response, scl_file_name)

    def test_generate_all_answer(question_folder:str, scl_folder:str):
        for file in os.listdir(question_folder):
            if file.endswith('.json'):
                question_file = os.path.join(question_folder, file)
                scl_file = os.path.join(scl_folder, file.split('.')[0]+"_glm.scl")
                with open(question_file, 'r', encoding='utf_8_sig') as f:
                    json_data = json.load(f)
                    if json_data["type"] == "FUNCTION":
                      scl_code_generator = SCLCodeGeneratorForFunction()
                      logging.info(f"Generate function code for %s", file)
                    else:
                      scl_code_generator = SCLCodeGenerator()
                      logging.info("Generate function block code for %s", file)
                    response = scl_code_generator.generate_code(json_data)
                    scl_code_generator.save(response, scl_file)
                    logging.info("Code generated for %s", file)

    # 单条生成，会在tmp下生成一个scl文件
    test_json_file = "pre_round_questions\FB_SplitNumber.json"
    scl_code = "tmp/compile_test.scl"
    test_generate_one_answer(test_json_file, scl_code)

    #批量生成，会在tmp下生成以题目名命名的scl文件
    # test_json_folder = "pre_round_questions"
    # scl_folder = "tmp"
    # test_generate_all_answer(test_json_folder, scl_folder)



    