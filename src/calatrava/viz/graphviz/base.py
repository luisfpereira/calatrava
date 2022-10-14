
from abc import ABCMeta, abstractmethod


class BaseRecordCreator(metaclass=ABCMeta):

    def __init__(self, default_styles, styles=None,):

        self.styles = default_styles

        if styles is not None:
            self._update_styles(styles)

    def _update_styles(self, styles):
        self.styles.update(styles)
        for key, value in styles.items():
            self.styles[key].update(value)

    @abstractmethod
    def create_node(self, dot, *args, **kwargs):
        pass
