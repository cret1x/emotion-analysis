import argparse
from os import listdir
from os.path import isfile, join
from time import sleep
from app.utils.utility_functions import (
    validate_input,
    validate_file_input,
    generate_textual_report_from_result_dictionary,
    generate_latex_report_from_result_dictionary,
)
import pylatex.errors
from app.emotions_measurer.measurer import EmotionsMeasurer


class CommandLine:
    def __init__(self) -> None:
        parser = argparse.ArgumentParser(description='Parser description')
        parser.add_argument(
            '-i',
            '--input',
            help = 'Provide input folder for emotion analysis',
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
        folder = ''
        threads_amount = ''
        if argument.input:
            folder = argument.input
            matched_argument = True
        if argument.threads:
            threads_amount = argument.threads
            matched_argument = True
        if matched_argument:
            input_valid, message = validate_file_input(
                folder,
                threads_amount,
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
            onlyfiles = [
                f for f in listdir(folder) \
                    if isfile(join(folder, f))
            ]
            for filename in onlyfiles:
                if filename.lower().endswith('mp4'):
                    print(f'[INFO] Starting to analyze emotions in file: {filename}')
                    frame_analyzer = EmotionsMeasurer(
                        join(folder, filename),
                        threads_numeric,
                        None,
                    )
                    frame_analyzer.analyse_prepared_video()
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
                            filename,
                        )
                    except Exception as ex:
                        print(
                            '[WARNING] Exception raised while generating latex report: '
                            f'{ex}.'
                        )


if __name__ == '__main__':
    app = CommandLine()
