"""Application state management."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from dynamic_input import DynamicInputHandler
from nn import NeuralNet, TrainConfig
from pyramid_generator import PyramidGenerator


class Screen(Enum):
    MAIN_MENU = "main_menu"
    DATA_MENU = "data_menu"
    TRAIN_MENU = "train_menu"
    TEST_MENU = "test_menu"
    EXPORT_MENU = "export_menu"
    SETTINGS_MENU = "settings_menu"
    HELP = "help"
    PROGRESS = "progress"
    FORM = "form"
    PREVIEW = "preview"


@dataclass
class AppState:
    """Central application state."""

    # Data
    data: np.ndarray | None = None
    data_meta: list = field(default_factory=list)

    # Model
    model: NeuralNet | None = None
    train_losses: list[float] = field(default_factory=list)
    val_losses: list[float] = field(default_factory=list)
    total_epochs: int = 0
    last_validation: str = ""

    # Input handler
    input_handler: DynamicInputHandler = field(
        default_factory=lambda: DynamicInputHandler(max_vertices=12, coordinates_per_vertex=3)
    )
    pyramid_generator: PyramidGenerator = field(
        default_factory=lambda: PyramidGenerator(seed=42)
    )

    # Test vector
    test_vector: np.ndarray | None = None
    test_prediction: float | None = None
    test_expected: int | None = None

    # UI state
    current_screen: Screen = Screen.MAIN_MENU
    # Stack of screens to return to via Esc/back. The top entry is the screen
    # we came from; GoBack pops it. A real stack (instead of a single
    # previous_screen slot) keeps back-navigation working across arbitrary
    # chains like Main → Data → Form → Preview.
    nav_stack: list[Screen] = field(default_factory=list)
    status_message: str = ""
    error_message: str = ""

    # Training config
    train_config: TrainConfig = field(
        default_factory=lambda: TrainConfig(epochs=1000, learning_rate=0.1, val_split=0.2, seed=42)
    )
    hidden_size: int = 32
    continue_training: bool = False

    # Settings
    max_vertices: int = 12
    language: str = "en"
    use_nerd_font: bool | None = None
    use_color: bool | None = None

    def reset_model(self) -> None:
        self.model = None
        self.train_losses = []
        self.val_losses = []
        self.total_epochs = 0
        self.last_validation = ""

    def can_continue_training(self, input_size: int, hidden_size: int) -> bool:
        return (
            self.model is not None
            and self.model.input_size == input_size
            and self.model.hidden_size == hidden_size
        )


# Action types for state updates
class Action:
    pass


@dataclass
class SetScreen(Action):
    screen: Screen


@dataclass
class GoBack(Action):
    pass


@dataclass
class SetData(Action):
    data: np.ndarray
    meta: list = field(default_factory=list)


@dataclass
class SetModel(Action):
    model: NeuralNet


@dataclass
class AddTrainingLoss(Action):
    train_loss: float
    val_loss: float


@dataclass
class SetValidation(Action):
    message: str


@dataclass
class SetStatus(Action):
    message: str


@dataclass
class SetError(Action):
    message: str


@dataclass
class ClearMessages(Action):
    pass


@dataclass
class SetTestVector(Action):
    vector: np.ndarray
    expected: int | None = None


@dataclass
class SetTestPrediction(Action):
    prediction: float


@dataclass
class UpdateConfig(Action):
    config: TrainConfig


@dataclass
class SetVertices(Action):
    vertices: int


def reducer(state: AppState, action: Action) -> AppState:
    """Pure state reducer."""
    new_state = AppState(
        data=state.data,
        data_meta=state.data_meta,
        model=state.model,
        train_losses=state.train_losses.copy(),
        val_losses=state.val_losses.copy(),
        total_epochs=state.total_epochs,
        last_validation=state.last_validation,
        input_handler=state.input_handler,
        pyramid_generator=state.pyramid_generator,
        test_vector=state.test_vector,
        test_prediction=state.test_prediction,
        test_expected=state.test_expected,
        current_screen=state.current_screen,
        nav_stack=state.nav_stack.copy(),
        status_message=state.status_message,
        error_message=state.error_message,
        train_config=state.train_config,
        hidden_size=state.hidden_size,
        continue_training=state.continue_training,
        max_vertices=state.max_vertices,
        language=state.language,
        use_nerd_font=state.use_nerd_font,
        use_color=state.use_color,
    )

    if isinstance(action, SetScreen):
        new_state.current_screen = action.screen
        if action.screen != state.current_screen:
            stack = state.nav_stack.copy()
            if not stack or stack[-1] != state.current_screen:
                stack.append(state.current_screen)
            new_state.nav_stack = stack

    elif isinstance(action, GoBack):
        if state.nav_stack:
            new_state.current_screen = state.nav_stack[-1]
            new_state.nav_stack = state.nav_stack[:-1]

    elif isinstance(action, SetData):
        new_state.data = action.data
        new_state.data_meta = action.meta
        new_state.reset_model()
        new_state.test_vector = None
        new_state.test_prediction = None
        new_state.test_expected = None

        # Update input handler
        if action.data is not None and action.data.ndim == 2 and action.data.shape[1] >= 2:
            feature_count = action.data.shape[1] - 1
            coords_per_vertex = new_state.input_handler.coordinates_per_vertex
            extra_features = 4
            coord_feature_count = max(feature_count - extra_features, 0)
            estimated_vertices = max(5, int(np.ceil(coord_feature_count / coords_per_vertex)))
            new_state.input_handler.max_vertices = estimated_vertices
            new_state.max_vertices = estimated_vertices

    elif isinstance(action, SetModel):
        new_state.model = action.model

    elif isinstance(action, AddTrainingLoss):
        new_state.train_losses.append(action.train_loss)
        new_state.val_losses.append(action.val_loss)
        new_state.total_epochs += 1

    elif isinstance(action, SetValidation):
        new_state.last_validation = action.message
        new_state.status_message = action.message

    elif isinstance(action, SetStatus):
        new_state.status_message = action.message
        new_state.error_message = ""

    elif isinstance(action, SetError):
        new_state.error_message = action.message

    elif isinstance(action, ClearMessages):
        new_state.status_message = ""
        new_state.error_message = ""

    elif isinstance(action, SetTestVector):
        new_state.test_vector = action.vector
        new_state.test_expected = action.expected
        new_state.test_prediction = None

    elif isinstance(action, SetTestPrediction):
        new_state.test_prediction = action.prediction

    elif isinstance(action, UpdateConfig):
        new_state.train_config = action.config

    elif isinstance(action, SetVertices):
        new_state.max_vertices = action.vertices
        new_state.input_handler.max_vertices = action.vertices

    return new_state
