from django.contrib import admin

from learning_materials.models import FlashcardModel, Cardset

# Register your models here.
admin.site.register(FlashcardModel)
admin.site.register(Cardset)
