from typing import List, Optional

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
import json

# ===== Import list of characteristics =====

charlist = []
with open('char_lists/list_followup.txt', 'r') as fp:
    charlist = fp.read().split(',')

# ===== Define schema =====

class PlantCharacteristic(BaseModel):
    """A characteristic of a plant species extracted from a botanical description."""

    characteristic: str = Field(
        default = None, description = "Name of the characteristic written in all lowercase; for example, 'fruit color' or 'plant height'"
    )
    value: str = Field(
        default = None, description = "The corresponding value for the characteristic; for example, '15-30 cm', '2-5', or 'red'"
    )

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

class Species(BaseModel):
    """Extracted list of characteristics about the provided plant species."""

    traits: List[PlantCharacteristic]

# ===== Define custom prompt =====

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
"""
You are a diligent robot assistant made by a botanist. You have expert knowledge of botanical terminology.
Your goal is to transcribe the given botanical description of plant characteristics.
You must include all the characteristics mentioned in the description.
""",
        ),
        # Please see the how-to about improving performance with
        # reference examples.
        # MessagesPlaceholder('examples'),
        ("human", "{text}"),
    ]
)

def main():
    

    # ===== Extract info with Ollama running on HPC =====

    llm = ChatGroq(
        model = "mixtral-8x7b-32768",
        temperature = 0,
        max_tokens = None,
        timeout = None,
        max_retries = 2
    )

    runnable = prompt | llm.with_structured_output(schema = Species, include_raw = True)

    text = "Herbs 0.2-0.9 m tall, erect. Stems 2-7 mm in diameter at base of plant, green to green mottled with purple, usually unwinged, glabrous; tubers typically moniliform (multiple tubers arranged along the stolon like beads on a necklace).Sympodial units tri- to plurifoliate, not geminate.Leaves odd-pinnate, the blades 3-9 x 1.5-5 cm, dark green adaxially, light green abaxially, coriaceous, glabrous to glabrescent adaxially with white short hairs, glabrous abaxially; lateral leaflet pairs 4-6, decreasing in size toward the leaf base, with the terminal leaflet subequal to the laterals; most distal lateral leaflets 0.8-2.6 x 0.2-0.5 cm, elliptic, the apex acute to acuminate, the base typically petiolulate and attenuate to rounded, symmetric, sometimes with secondary interjected leaflets in the petiolule; terminal leaflet 1.2-3.5 x 0.3-0.5 cm, elliptic, the apex acute to acuminate, the base cuneate; interjected leaflets 0-27, usually decurrent onto the rachis, lanceolate; petioles 0-0.3 cm, glabrous. Pseudostipules 3-4 mm long, glabrous.Inflorescences 2.5-8 cm, terminal with a subtending axillary bud, generally in distal half of the plant, forked, with 2-20 flowers, with all flowers apparently perfect, the axes glabrous; peduncle 1-12 cm long; pedicels 14-38 mm long in flower and fruit, spaced 3-5 mm apart, articulated high in the distal half.Flowers homostylous, 5-merous. Calyx 3-5 mm long, the tube 1-2 mm, the lobes 1-2 mm, usually ovate, with linear acumens 1-2 mm long, glabrous. Corolla 2.8-4.2 cm in diameter, pentagonal to rotate, lilac to blue, the tube 1-2 mm long, the acumens 2-3 mm long, the corolla edges flat, not folded dorsally, glabrous abaxially and adaxially. Stamens with the filaments 1-2 mm long; anthers 5-7 mm long, lanceolate, connivent, yellow, poricidal at the tips, the pores lengthening to slits with age. Ovary glabrous; style 3-10 mm x ca. 1 mm, exceeding stamens by 1-5 mm, straight, glabrous; stigma clavate to capitate.Fruit a globose to ovoid berry, 1-2.5 cm wide, 1.6-2.5 mm long, medium to deep green with dark green stripes or tiny white dots when ripe, glabrous.Seeds from living specimens ovoid and ca. 2 mm long, whitish to greenish in fresh condition and drying brownish, with a thick covering of “hair-like” lateral walls of the testal cells that make the seeds mucilaginous when wet, green-white throughout; testal cells honeycomb-shaped when lateral walls removed by enzyme digestion."

    species = runnable.invoke({"text": text})['parsed']

    for trait in species.traits:
        print(trait.to_json())

if __name__ == '__main__':
    main()