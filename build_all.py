import sys
import subprocess
import os

class Command:
    def __init__(self, kb, km) -> None:
        self.kb = kb
        self.km = km
        self.arguments = []
        self.left_pointing_device = None
        self.right_pointing_device = None
        self.oled = None

    def prepend_argument(self, argument):
        self.arguments.insert(0, argument)
        self.arguments.insert(0, '-e')

    def set_pointing(self, kind, side):
        if side == 'left':
            self.left_pointing_device = kind
        elif side == 'right':
            self.right_pointing_device = kind
        else:
            raise ValueError('Invalid side: {}'.format(side))

    def add_argument(self, argument):
        self.arguments.append('-e')
        self.arguments.append(argument)

    def add_argument_raw(self, argument):
        self.arguments.append(argument)

    def build(self):
        return ' '.join(self.build_list())

    def build_list(self):
        return ['make', f'{self.kb}:{self.km}'] + self.arguments

    def file_name(self):
        parts = []
        parts.append(self.kb.replace('/', '_'))
        parts.append(self.km)

        if not self.kb.startswith('keyball'):
            if self.left_pointing_device:
                parts.append(self.left_pointing_device)
            elif self.oled:
                parts.append('oled')
            else:
                parts.append('none')

            if self.right_pointing_device:
                parts.append(self.right_pointing_device)
            elif self.oled:
                parts.append('oled')
            else:
                parts.append('none')

        for argument in self.arguments:
            if argument.startswith('SIDE='):
                side = argument[len('SIDE='):]
                parts.append('flash_on_' + side)
        return '_'.join(parts)

def build_commands():
    commands = []
    skip_pointing_devices =[('trackpoint', 'trackpoint'), ('cirque35', 'cirque40'), ('cirque40', 'cirque35')]
    for kb in ['crkbd/rev1', 'holykeebs/spankbd', 'lily58/rev1', 'holykeebs/sweeq']:
        for left_pointing_device in ['trackpoint', 'trackball', 'cirque35', 'cirque40', 'tps43', '']:
            for right_pointing_device in ['trackpoint', 'trackball', 'cirque35', 'cirque40', 'tps43', '']:
                if (left_pointing_device, right_pointing_device) in skip_pointing_devices:
                    print('Skipping configuration: ', left_pointing_device, right_pointing_device)
                    continue
                if left_pointing_device and right_pointing_device:
                    for side in ('left', 'right'):
                        command = Command(kb, 'via')
                        command.set_pointing(left_pointing_device, 'left')
                        command.set_pointing(right_pointing_device, 'right')
                        command.add_argument(f'POINTING_DEVICE={left_pointing_device}_{right_pointing_device}')
                        command.add_argument(f'SIDE={side}')
                        if left_pointing_device == 'trackball' or right_pointing_device == 'trackball':
                            command.add_argument(f'TRACKBALL_RGB_RAINBOW=yes')
                        commands.append(command)
                else:
                    for with_oled in [True, False]:
                        command = Command(kb, 'via')
                        if with_oled:
                            command.oled = True
                            command.add_argument(f'OLED=yes')
                            command.add_argument(f'OLED_FLIP=yes')
                        if left_pointing_device:
                            command.set_pointing(left_pointing_device, 'left')
                            command.add_argument(f'POINTING_DEVICE={left_pointing_device}')
                            command.add_argument(f'POINTING_DEVICE_POSITION=left')
                            if left_pointing_device == 'trackball':
                                command.add_argument(f'TRACKBALL_RGB_RAINBOW=yes')
                        elif right_pointing_device:
                            command.set_pointing(right_pointing_device, 'right')
                            command.add_argument(f'POINTING_DEVICE={right_pointing_device}')
                            command.add_argument(f'POINTING_DEVICE_POSITION=right')
                            if right_pointing_device == 'trackball':
                                command.add_argument(f'TRACKBALL_RGB_RAINBOW=yes')
                        else:
                            pass

                        commands.append(command)

    return commands

def main() -> int:
    commands = [
        Command('keyball/keyball39', 'via'),
        Command('keyball/keyball44', 'via'),
        Command('keyball/keyball61', 'via'),
    ]
    for command in build_commands():
        command.prepend_argument('USER_NAME=holykeebs')
        commands.append(command)

    os.makedirs('build_all', exist_ok=True)
    commands_file = open('build_all/commands.txt', 'w')
    for command in commands:
        if os.path.exists(f'build_all/{command.file_name()}.uf2'):
            print(f'Skipping {command.file_name()} (already built)')
            continue

        command.add_argument_raw('-j20')
        command.prepend_argument(f'TARGET={command.file_name()}')
        print(f'Making {command.file_name()}: {command.build()}')
        run_command_check_output(command.build().split())
        # move the file to build_all
        os.rename(f'{command.file_name()}.uf2', f'build_all/{command.file_name()}.uf2')
        commands_file.write(f'{command.file_name()}: {command.build()}\n')
    return 0

def run_command_check_output(command):
    print(f'Running: {command}')
    output = subprocess.check_output(command)
    return output

if __name__ == '__main__':
    sys.exit(main())
