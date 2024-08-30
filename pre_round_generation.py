from scl_code_generator import SCLCodeGenerator
import json
import os
import logging
import datetime
import shutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
    )

def generate_code(json_file):
    scl_code_generator = SCLCodeGenerator()
    code = ""
    with open(json_file, 'r', encoding='utf_8_sig') as file:
        json_question = json.load(file)
        code = scl_code_generator.generate_code(json_question)
    return code

def generate_answer_file(json_file_path, answer_file_path, answer_file_name):
    """
    生成答案文件。
    答案文件是一个jsonl文件，每一行对应一个题目。
    每一行是一个json，有两个成员，第一个成员"name"对应题目名，第二个成员"code"对应生成的代码。
    """
    answer_file = os.path.join(answer_file_path, answer_file_name)
    with open(answer_file, 'w', encoding='utf-8') as answer:
        for file in os.listdir(json_file_path):
            if file.endswith('.json'):
                answer_json = {}
                logging.info("Generating code for %s", file)
                code = generate_code(os.path.join(json_file_path, file))
                file_name = file.split('.')[0]
                answer_json['name'] = file_name
                answer_json['code'] = code
                json.dump(answer_json, answer, separators=(',', ':'))
                with open(os.path.join(answer_file_path, file_name + '.scl'), 'w', encoding='utf-8-sig') as f:
                    f.write(code)
                answer.write('\n')
        logging.info("Answer file generated.")
            

if __name__ == "__main__":
    pre_round_question_path = "./pre_round_questions"
    submits_path = "./pre_round_submits"
    date = datetime.datetime.now().strftime('%m%d')
    path_today = os.path.join(submits_path, date)
    if os.path.isdir(path_today):
        shutil.rmtree(path_today)
    os.mkdir(path_today)
    answer_file_name = "answer"+date+".jsonl"

    generate_answer_file(pre_round_question_path, path_today, answer_file_name)
    