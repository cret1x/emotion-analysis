import argparse
from time import sleep
from app.utils.utility_functions import (
    validate_input,
    generate_textual_report_from_result_dictionary,
    generate_latex_report_from_result_dictionary,
)
import pylatex.errors
from app.emotions_measurer.measurer import EmotionsMeasurer


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
        parser.add_argument(
            '-m',
            '--mode',
            help = 'Change mode to real time evaluation.',
            required = False,
            default = '',
        )
        argument = parser.parse_args()
        matched_argument = False
        filename = ''
        threads_amount = ''
        mode = ''
        if argument.Help:
            print('''
[INFO] Instruction for emotions analyzer:
python emotionsAnalysis.py -i <file_destination> -t <threads_amount> -m <mode>
'''
            )
            return
        if argument.input:
            filename = argument.input
            matched_argument = True
        if argument.threads:
            threads_amount = argument.threads
            matched_argument = True
        if argument.mode:
            mode = argument.mode
            matched_argument = True
        if matched_argument:
            input_valid, message = validate_input(
                filename,
                threads_amount,
                mode
            )
            if not input_valid:
                print(
                    '[ERROR] Provided invalid input. Try again. '
                    f'Details: {message}'
                )
                return
            print('[INFO] Valid input provided.')
            threads_numeric = int(threads_amount) \
                if threads_amount != '' else None
            frame_analyzer = EmotionsMeasurer(
                filename,
                threads_numeric,
                mode
            )
            if mode != 'realtime':
                frame_analyzer.analyse_prepared_video()
            else:
                print('[INFO] Some ground info before realtime analysis starts:')
                print('[INFO] To quit, press "q" on the keyboard.')
                print(
                    '[INFO] Considering the analysis is realtime, '
                    'the output may differ based on the machine.')
                print('[INFO] The camera will start in:')
                for i in range(10, 0, -1):
                    print(i)
                    sleep(1)
                frame_analyzer.analyze_realtime()
            generate_textual_report_from_result_dictionary(
                frame_analyzer._emotions_occurances,
                frame_analyzer._looked_away,
                frame_analyzer._frames_amount,
            )
            try:
                generate_latex_report_from_result_dictionary(
                    frame_analyzer._emotions_occurances,
                    frame_analyzer._looked_away,
                    frame_analyzer._frames_amount,
                    frame_analyzer._coordinates,
                    frame_analyzer._best_performance,
                )
            except Exception as ex:
                print(
                    '[WARNING] Exception raised while generating latex report: '
                    f'{ex}.'
                )
        else:
            print('''
[INFO] Instruction for emotions analyzer:
python emotionsAnalysis.py -i <file_destination> -t <threads_amount> -m <mode>
'''
            )


if __name__ == '__main__':
    app = CommandLine()
