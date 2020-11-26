import logging
import platform
import types

try:
    import colorama
    colorama.init()

    defaultColorMap = {
        logging.INFO: colorama.Fore.BLUE,
        logging.WARNING: colorama.Fore.YELLOW,
        logging.ERROR: colorama.Fore.RED,
        'ENDC': colorama.Style.RESET_ALL
    }
    COLORAMA_AVAILABLE = True
except:
    defaultColorMap = {
        logging.INFO: '\033[94m',  # blue
        logging.WARNING: '\033[93m',  # yellow
        logging.ERROR: '\033[91m',  # red
        'ENDC': '\033[0m',
    }
    COLORAMA_AVAILABLE = False


def colored_info(logger, msg, *args, **kwargs):
    logger.info_(logger.infoColor + msg + logger.endc, *args, **kwargs)


def colored_warning(logger, msg, *args, **kwargs):
    logger.warning_(logger.warningColor + msg + logger.endc, *args, **kwargs)


def colored_error(logger, msg, *args, **kwargs):
    logger.error_(logger.errorColor + msg + logger.endc, *args, **kwargs)


class ColoredLogging:

    @staticmethod
    def patchLogger(baseLogger: logging.Logger, colormap=None):
        colormap = colormap if colormap is not None else defaultColorMap

        if (not COLORAMA_AVAILABLE) and platform.uname()[0].lower().startswith('win'):
            return

        baseLogger.infoColor = colormap[logging.INFO]
        baseLogger.warningColor = colormap[logging.WARNING]
        baseLogger.errorColor = colormap[logging.ERROR]
        baseLogger.endc = colormap['ENDC']

        baseLogger.info_ = baseLogger.info
        baseLogger.warning_ = baseLogger.warning
        baseLogger.error_ = baseLogger.error

        baseLogger.info = types.MethodType(colored_info, baseLogger)
        baseLogger.warning = types.MethodType(colored_warning, baseLogger)
        baseLogger.error = types.MethodType(colored_error, baseLogger)
