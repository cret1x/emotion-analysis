import argparse
from typing import Optional
from app.emotions_measurer.measurer import EmotionsMeasurer
from app.utils.utility_functions import validate_input

class CommandLine:
    def __init__(self) -> None:
        parser = argparse.ArgumentParser(description='Parser description')
        parser.add_argument(
            '-H',
            '--Help',
            help = 'Get help on command line arguments',
            required = False,
            default = '',
        )
        parser.add_argument(
            '-i',
            '--input',
            help = 'Provide input file for emotion analysis',
            required = False,
            default = '',
        )
        parser.add_argument(
            '-t',
            '--threads',
            help = 'Provide the amount of threads to run the analysis on',
            required = False,
            default='',
        )
        argument = parser.parse_args()
        matched_argument = False
        filename = ''
        threads_amount = ''
        if argument.Help:
            print('''
Instruction for emotions analyzer:
python emotionsAnalysis.py -i <file_destination> -t <threads_amount>
'''
            )
            return
        if argument.input:
            filename = argument.input
            matched_argument = True
        if argument.threads:
            threads_amount = argument.threads
            matched_argument = True
        if matched_argument:
            input_valid = validate_input(filename, threads_amount)
            if not input_valid:
                print('Provided invalid input. Try again.')
                return
            print('Valid input provided.')
            threads_numeric = int(threads_amount) if threads_amount != '' else None
            frame_analyzer = EmotionsMeasurer(filename, threads_numeric)
            frame_analyzer.analyse_prepared_video()
        else:
            print('''
Instruction for emotions analyzer:
python emotionsAnalysis.py -i <file_destination> -t <threads_amount>
'''
            )


if __name__ == '__main__':
    app = CommandLine()
