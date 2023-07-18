# Copyright (c) Alibaba, Inc. and its affiliates.
import os

from llmuses.predictors.openai_gpt_predictor import OpenaiGptPredictor
from llmuses.tasks import BaseTask
from llmuses.utils.logger import get_logger
from llmuses.utils.utils import jsonl_dump_data, jsonl_to_list

logger = get_logger()


class TaskEvalGpt35Completion(BaseTask):

    MODEL_NAME = 'gpt-3.5-turbo'

    def __init__(self, **kwargs):

        if not kwargs:
            self.task_cfg = self._get_default_cfg()
        else:
            self.task_cfg = kwargs

        self.question_list = jsonl_to_list(self.task_cfg.pop('question_file'))
        self.ans_file = self.task_cfg.pop('output_file', None)
        self.gpt_predictor = OpenaiGptPredictor()

    def _get_default_cfg(self):
        default_cfg = dict(
            model=self.MODEL_NAME,
            question_file='llmuses/registry/data/arena/question.jsonl',
            max_tokens=1024,
            temperature=0.2,
            output_file='llmuses/registry/data/arena/answers/answer_gpt35.jsonl'
        )
        return default_cfg

    def run_dummy(self):
        res_list = list()
        for question in self.question_list:
            ans = {
                'question_id': question['question_id'],
                'text': question['text'],
                'category': question['category'],
                'model_id': self.MODEL_NAME,
                'metadata': {},
                'answer': 'This is a dummy answer, only for test.'
            }
            res_list.append(ans)

        os.makedirs(os.path.dirname(self.ans_file), exist_ok=True)
        jsonl_dump_data(res_list, self.ans_file)

        return self.ans_file

    def run(self):
        res_list = list()

        for question in self.question_list:
            input_cfg = dict()
            input_cfg.update(self.task_cfg)
            input_cfg['sys_prompt'] = ''
            input_cfg['user_prompt'] = question['text']

            try:
                resp = self.gpt_predictor.predict(**input_cfg)
                ans_text = resp['ans_text']
                model_id = resp['model_id']
            except Exception as e:
                logger.warning(f'GPT-3.5-turbo failed to predict: {e}')
                ans_text = ''
                model_id = input_cfg['model']

            ans = {
                'question_id': question['question_id'],
                'text': question['text'],
                'category': question['category'],
                'model_id': model_id,
                'metadata': {},
                'answer': ans_text,
            }
            res_list.append(ans)

        os.makedirs(os.path.dirname(self.ans_file), exist_ok=True)
        jsonl_dump_data(res_list, self.ans_file)

        return self.ans_file
