import json
import logging
import asyncio
from typing import Any, Callable
from fastapi import Request

from open_webui.models.memories import Memories
from open_webui.retrieval.vector.connector import VECTOR_DB_CLIENT
from open_webui.env import SRC_LOG_LEVELS
from open_webui.models.users import Users

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])
PERIOD_LENGTH = 3

async def extract_and_save_memory(
    request: Request, 
    form_data: dict, 
    user: Any, 
    generate_completion_func: Callable
):
    """
    Periodically extracts educational facts from the chat and saves them to the vector DB.
    """
    try:
        messages = form_data.get("messages", [])
        
        # 1. Periodic Check: Only run every PERIOD_LENGTH user messages
        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages or len(user_messages) % PERIOD_LENGTH != 0:
            log.info(f"[MEMORIES] ignoring collection, number of messages {len(user_messages)}")
            return


        # 2. Check User Preferences: Respect the opt-out toggle
        db_user = Users.get_user_by_id(user.id)
        if db_user:
            db_user = db_user.model_dump()
            user_settings = db_user.get("settings", {})
            ui_settings = user_settings.get("ui", {})
            memory_enabled = ui_settings.get("memory", False)
            
            if not memory_enabled:
                log.info(f"[MEMORIES] User {user.id} has memory disabled. Skipping extraction.")
                return

        log.info("[MEMORIES] Memory activated, running periodic background memory collection...")
        log.info(f"[MEMORIES] starting collection, number of messages {len(user_messages)}")

        # 3. Fetch existing memories to prevent duplicates
        existing_memories = Memories.get_memories_by_user_id(user.id)
        
        # Format them into a bulleted list string
        if existing_memories:
            existing_facts_list = "\n".join([f"- {mem.content}" for mem in existing_memories])
        else:
            existing_facts_list = "Aucune mémoire enregistrée pour le moment."

        # 4. Format the transcript (grab the last PERIOD_LENGTH messages for context)
        transcript = ""
        for m in messages[-PERIOD_LENGTH:]:
            role = m.get("role", "unknown")
            content = m.get("content", "")
            transcript += f"{role.capitalize()}: {content}\n\n"

        # 5. Memory collection prompt
        system_prompt = f"""
        Tu es l'analyste de mémoire en arrière-plan pour l'IA Compagnon d'Oreegami. 
        Ton rôle est d'analyser la conversation et d'extraire UNIQUEMENT des faits qualitatifs et durables concernant la pédagogie, la progression, et le contexte professionnel de l'apprenant. 

        Toutes les mémoires doivent être rédigées à la 3ème personne ("L'apprenant...", "L'utilisateur...").

        Ce que tu dois CHERCHER ET MÉMORISER (Faits durables) :
        1. Préférences d'interaction : Comment l'apprenant souhaite que l'IA lui réponde (ex: ton direct, réponses brèves, utilisation de métaphores, formatage en listes).
        2. Progression et Blocages : Avancement dans le e-learning, concepts maîtrisés, ou difficultés techniques récurrentes.
        3. Contexte Professionnel (Le ressenti) : La dynamique dans son entreprise (ex: se sent isolé, tâches répétitives, manager exigeant, nature des projets).
        4. Objectifs à long terme : Ambitions de carrière au-delà du diplôme actuel.

        Ce que tu dois STRICTEMENT IGNORER :
        - Les données administratives : Nom, genre, campus, nom de l'entreprise d'alternance, titre RNCP, dates. (Le système les connaît déjà).
        - Les actions éphémères : Salutations, états d'âme passagers ("je suis fatigué"), ou tâches à court terme ("je finis mon exercice ce soir"). 
        -> Pose-toi la question : "Cette information sera-t-elle utile pour un tuteur dans 3 mois ?" Si non, ignore-la.

        Voici les mémoires DÉJÀ ENREGISTRÉES pour cet utilisateur :
        {existing_facts_list}

        Règles à respecter :
        - NE PAS extraire une information si elle est déjà présente (ou sémantiquement identique) dans la liste des mémoires ci-dessus.
        - La mémoire doit être aussi concise que possible (une seule phrase factuelle).
        - Ne conserves que le fait le plus important (une seule mémoire au maximum doit être extraite).
        - Génères UNIQUEMENT un tableau JSON valide de chaînes de caractères.
        - S'il n'y a rien de pertinent à mémoriser OU si l'information est DÉJÀ mémorisée, renvois strictement un tableau vide : []

        Exemples de mémoires VALIDES :
        - ["L'apprenant préfère que les concepts techniques soient expliqués directement et brièvement."]
        - ["L'utilisateur a des difficultés récurrentes à comprendre les requêtes SQL avec des jointures complexes."]
        - ["L'apprenant se sent isolé dans son alternance car il est le seul profil technique de l'équipe."]
        - ["L'utilisateur a atteint le chapitre 4 du module sur le Machine Learning."]

        Exemples d'informations à IGNORER (Tableau vide []) :
        - Demandes administratives ("Je m'appelle Thomas et je suis sur le campus de Paris.")
        - Actions courtes ("Je vais passer mon examen blanc demain matin.")

        *IMPORTANT* 
        Si l'utilisateur demande explicitement à l'IA de retenir ou d'oublier une façon de faire, sauvegardes-la impérativement (sauf si elle existe déjà).
        """
        # 6. Create the silent extraction payload
        payload = {
            "model": "",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Conversation:\n{transcript}"}
            ],
            "stream": False
        }

        # 7. Ask the LLM (using the passed generation function)
        response = await generate_completion_func(request, payload, user)
        
        content = ""
        if isinstance(response, dict):
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # 8. Parse the JSON array
        start = content.find('[')
        end = content.rfind(']')
        if start == -1 or end == -1:
            log.error(f"[MEMORIES] memory parsing error, Raw LLM response: {content}")
            return
            
        facts = json.loads(content[start:end+1])
        log.info(f"[MEMORIES] LLM evaluated the chat and decided to extract: {facts}")

        # 9. Save to the vector database
        for fact in facts:
            if not isinstance(fact, str): continue
            
            memory = Memories.insert_new_memory(user.id, fact)
            VECTOR_DB_CLIENT.upsert(
                collection_name=f"user-memory-{user.id}",
                items=[{
                    "id": memory.id,
                    "text": memory.content,
                    "vector": request.app.state.EMBEDDING_FUNCTION(memory.content, user=user),
                    "metadata": {"created_at": memory.created_at},
                }],
            )
            log.info(f"[MEMORIES] Oreegami Memory Saved: {fact}")

    except Exception as e:
        log.error(f"Background memory extraction failed: {e}")