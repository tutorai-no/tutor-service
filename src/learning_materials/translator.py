from learning_materials.learning_resources import Flashcard
from learning_materials.models import CardsetModel, FlashcardModel

def translate_flashcard_to_orm_model(flashcard: Flashcard, cardset: CardsetModel) -> Flashcard:
    """Translate a Flashcard Pydantic model to an ORM model."""
    return Flashcard.objects.create(
        front=flashcard.front,
        back=flashcard.back,
        cardset=cardset
    )