from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('learning_materials', '0010_clusterelement_dimensions_clusterelement_z'),
    ]
    
    operations = [
        migrations.RunSQL(
            """
            -- Create uuid extension FIRST
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            
            -- Create Cardset table
            CREATE TABLE IF NOT EXISTS "learning_materials_cardset" (
                "id" uuid NOT NULL PRIMARY KEY DEFAULT uuid_generate_v4(),
                "name" varchar(100) NOT NULL,
                "description" text NOT NULL,
                "subject" varchar(1000) NULL,
                "start_page" integer NULL,
                "end_page" integer NULL,
                "course_id" uuid NULL,
                "user_id" uuid NOT NULL,
                "created_at" timestamp with time zone NULL,
                "updated_at" timestamp with time zone NULL
            );
            
            -- Create QuizModel table
            CREATE TABLE IF NOT EXISTS "learning_materials_quizmodel" (
                "id" uuid NOT NULL PRIMARY KEY DEFAULT uuid_generate_v4(),
                "name" varchar(100) NOT NULL,
                "document_name" varchar(100) NOT NULL,
                "subject" varchar(1000) NULL,
                "start_page" integer NULL,
                "end_page" integer NULL,
                "course_id" uuid NULL,
                "user_id" uuid NOT NULL,
                "created_at" timestamp with time zone NULL,
                "updated_at" timestamp with time zone NULL
            );
            
            -- Create FlashcardModel table WITHOUT mastery field
            CREATE TABLE IF NOT EXISTS "learning_materials_flashcardmodel" (
                "id" uuid NOT NULL PRIMARY KEY DEFAULT uuid_generate_v4(),
                "front" text NOT NULL,
                "back" text NOT NULL,
                "proficiency" integer NOT NULL,
                "time_of_next_review" timestamp with time zone NOT NULL,
                "cardset_id" uuid NOT NULL,
                "created_at" timestamp with time zone NULL,
                "updated_at" timestamp with time zone NULL,
                CONSTRAINT "learning_materials_flashcardmodel_cardset_id_fkey" FOREIGN KEY ("cardset_id")
                    REFERENCES "learning_materials_cardset" ("id") ON DELETE CASCADE
            );
            
            -- Create QuestionAnswerModel table
            CREATE TABLE IF NOT EXISTS "learning_materials_questionanswermodel" (
                "id" uuid NOT NULL PRIMARY KEY DEFAULT uuid_generate_v4(),
                "question" text NOT NULL,
                "answer" text NOT NULL,
                "quiz_id" uuid NOT NULL,
                "created_at" timestamp with time zone NULL,
                "updated_at" timestamp with time zone NULL,
                CONSTRAINT "learning_materials_questionanswermodel_quiz_id_fkey" FOREIGN KEY ("quiz_id")
                    REFERENCES "learning_materials_quizmodel" ("id") ON DELETE CASCADE
            );
            
            -- Create MultipleChoiceQuestionModel table
            CREATE TABLE IF NOT EXISTS "learning_materials_multiplechoicequestionmodel" (
                "id" uuid NOT NULL PRIMARY KEY DEFAULT uuid_generate_v4(),
                "question" text NOT NULL,
                "options" jsonb NOT NULL,
                "answer" text NOT NULL,
                "quiz_id" uuid NOT NULL,
                "created_at" timestamp with time zone NULL,
                "updated_at" timestamp with time zone NULL,
                CONSTRAINT "learning_materials_multiplechoicequestionmodel_quiz_id_fkey" FOREIGN KEY ("quiz_id")
                    REFERENCES "learning_materials_quizmodel" ("id") ON DELETE CASCADE
            );
            
            -- Rest of the tables...
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
    ]