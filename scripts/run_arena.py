# Copyright (c) Alibaba, Inc. and its affiliates.
# yapf: disable
# isort:skip_file
# flake8: noqa

import argparse
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evals.constants import EvalTaskConfig
from evals.evaluator.elo_rating_eval import EloRatingEvaluate
from evals.utils.logger import get_logger
from evals.utils.utils import get_obj_from_cfg, yaml_to_dict

logger = get_logger()


class ArenaWorkflow:

    def __init__(self, cfg_file: str, **kwargs):

        self.cfg_dict = yaml_to_dict(cfg_file)
        # logger.info(f'Config: {self.cfg_dict}')

        self.question_file: str = self.cfg_dict.get('question_file')

        self.answers_gen: dict = self.cfg_dict.get('answers_gen', {})
        for k in self.answers_gen.keys():
            self.answers_gen[k] = ArenaWorkflow._get_obj_from_cfg(
                self.answers_gen[k])

        self.reviews_gen: dict = self.cfg_dict.get('reviews_gen', {})
        self.reviewer_cfg: dict = ArenaWorkflow._get_obj_from_cfg(
            self.reviews_gen.get('reviewer', {}))
        self.prompt_file = os.path.abspath(self.reviews_gen.get('prompt_file'))
        self.review_file = os.path.abspath(self.reviews_gen.get('review_file'))

        self.elo_rating: dict = self.cfg_dict.get('elo_rating', {})
        self.report_file = os.path.abspath(self.elo_rating.get('report_file'))

    @staticmethod
    def _get_obj_from_cfg(obj_cfg: dict):
        cls_ref = obj_cfg.get(EvalTaskConfig.CLASS_REF, None)
        if not cls_ref:
            logger.warning(
                f'Class reference is not specified in config: {obj_cfg}')
            return obj_cfg

        cls = get_obj_from_cfg(cls_ref)
        obj_cfg[EvalTaskConfig.CLASS_REF] = cls

        return obj_cfg

    def get_answers(self):

        for model_name, cfg in self.answers_gen.items():
            enable = cfg.get(EvalTaskConfig.ENABLE, True)
            if not enable:
                logger.info(
                    f'Skip model {model_name} because it is not enabled.')
                continue

            model_cls = cfg.get(EvalTaskConfig.CLASS_REF)
            if not model_cls:
                logger.warning(
                    f'Skip model {model_name} because class reference '
                    f'is not specified.')
                continue
            model_args = cfg.get(EvalTaskConfig.CLASS_ARGS, {})

            input_kwargs = dict()
            input_kwargs['question_file'] = self.question_file
            input_kwargs['output_file'] = cfg.get('output_file')
            input_kwargs.update(model_args)
            model_obj = model_cls(**input_kwargs)

            model_obj.run_dummy()  # Note: only for test
            # model_obj.run()
            logger.info(f'Answers generated by model {model_name} '
                        f'are saved to {input_kwargs["output_file"]}.')

    def get_reviews(self):
        enable = self.reviews_gen.get(EvalTaskConfig.ENABLE, True)
        if enable:
            reviewer_cls = self.reviewer_cfg.get(EvalTaskConfig.CLASS_REF)
            if not reviewer_cls:
                logger.warning('Skip reviews generation because '
                               'class reference is not specified.')
                return
            reviewer_args = self.reviewer_cfg.get(EvalTaskConfig.CLASS_ARGS,
                                                  {})
            target_answers = self.reviews_gen.get('target_answers', [])
            target_answers = [
                os.path.abspath(file_path) for file_path in target_answers
            ]

            input_kwargs = dict(
                prompt_file=self.prompt_file,
                answer_file_list=target_answers,
                review_file=self.review_file,
                reviewer_args=reviewer_args)
            reviewer_obj = reviewer_cls(**input_kwargs)

            reviewer_obj.run()
            logger.info(f'Reviews generated by reviewer '
                        f'are saved to {self.review_file}.')

        else:
            logger.warning(
                'Skip reviews generation because it is not enabled.')

    def get_elo_rating(self):
        enable = self.elo_rating.get(EvalTaskConfig.ENABLE, True)
        if enable:
            metrics = ['elo']
            ae = EloRatingEvaluate(metrics=metrics)
            res_list = ae.run(self.review_file)
            elo_df = res_list[0]
            logger.info(f'ELO rating results:\n{elo_df}')
            elo_df.to_csv(self.report_file, index=True)
            logger.info(f'ELO rating results are saved to {self.report_file}.')
        else:
            logger.warning('Skip elo rating because it is not enabled.')

    def run(self):

        # Get all answers
        self.get_answers()

        # Get all reviews
        self.get_reviews()

        # Get ELO rating results
        self.get_elo_rating()

        logger.info('*** Arena workflow is finished. ***')


def main():

    # Usage: python run_arena.py -c /path/to/xxx_cfg_arena.yaml
    parser = argparse.ArgumentParser(
        description='LLMs evaluations with arena mode.')
    parser.add_argument(
        '-c', '--cfg-file', default='evals/registry/tasks/cfg_arena.yaml')
    args = parser.parse_args()
    logger.info(f'Config file: {args.cfg_file}')

    arena_workflow = ArenaWorkflow(cfg_file=args.cfg_file)
    arena_workflow.run()


if __name__ == '__main__':
    main()
