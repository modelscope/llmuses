# Copyright (c) Alibaba, Inc. and its affiliates.

import os
import sys

from llmuses.evaluator.rating_eval import RatingEvaluate

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    # Supported columns for model battles:
    # 'model_a', 'model_b', 'win', 'tstamp', 'language'
    review_data_path = os.path.join(os.getcwd(),
                                    'llmuses/registry/data/arena/reviews',
                                    'review_gpt4.jsonl')

    metrics = ['elo']
    ae = RatingEvaluate(metrics=metrics)
    res_list = ae.run(review_data_path)

    print(res_list[0])


if __name__ == '__main__':
    main()
