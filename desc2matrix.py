from ollama import Client

# Custom modelfile
modelfile="""
FROM llama3

PARAMETER temperature 0.1
"""

# Definitions of system and user prompts
system_prompt = """
You are a botanist who is processing text from botanical descriptions of plants. Your reponse includes only valid JSON format, with no introductory text.
"""
prompt = """
You are given botanical descriptions of plant species taken from published floras.
You extract the types of characteristics mentioned in the description and their corresponding values.
For each species, you must respond in JSON formatted as follows: {"species_name":"", "characteristics":""}.
The characteristics key in this JSON should be an array of JSON with name of the characteristic and the corresponding value formatted as follows: {"characteristic":"", "value":""}.
The JSON for the species should be collected together as an array.
Break down the characteristics as finely as possible so that each value is no longer than 7 words.
All species should have entries for all the characteristics mentioned. Do not omit any information included in the description.
Never include any introductory text other than the valid JSON.
"""
test_description_1 = """
Subshrub, ca. 3 m high, monoecious, pubescent, with both dendritic greyish trichomes, 0.1–0.4 mm long, and microscopic glandular trichomes. Stem erect, fl eshy, pubescent; internodes 1–3.5 cm long. Stipules 2.5–3 × 0.7–1.5 cm, lanceolate, apex apiculate, margin entire, pubescent, carinate, appressed, caducous. Leaves: petiole 6.3–11.6 cm long, cylindrical, pubescent; blade 13–18 × 19–28 cm, transversally elliptic, deeply lobed (lobes approximately half the length of their main vein), 6 or 7 lobes, asymmetric, basifi xed; base cordate; lobes with acute apex; margin serrulate; pubescent on both surfaces, more densely so on abaxial surface, discolorous, adaxial surface green, abaxial surface green-cinereous; venation actinodromous, 6 or 7 veins at base, slightly thickened. Infl orescence: dichasial cyme 32–39 cm long, ca. 180 flowers; peduncle 23.5– 27 cm long, cinereous; fi rst order bracts 4–6 × 1.5–2.5 mm, lanceolate, apex acuminate, margin entire, caducous. Staminate fl owers: pedicel 1–1.4 cm long, pilose; tepals 4, white, the outer pair larger 6–7.2 × 3–4 mm, ovate to elliptic, apex acute to obtuse, margin entire, concave, glabrescent on abaxial surface, the inner pair 5–6.2 × 1.8–2.3 mm, oblong to oblanceolate, apex obtuse to rounded, margin entire, concave, glabrous; androecium actinomorphic, stamens 32–48, fi laments 0.2–0.9 mm long, free, anthers 1–1.3 mm long, rimose, connective prolonged. Pistillate flowers [not seen]: bracteoles 2, opposite, borne on pedicel, just below ovary, caducous [scars seen on the pedicel from capsules]; styles 3, 1.6–2 mm long, bifi d, branches spirally-arranged, stigmatic papillae covering branches, stigmatic surface papillose, yellow [obtained from capsules]; ovary 5–6.7 mm long, trilocular, placentation axile, placenta entire [observed from capsules]. Capsules 6–7.5 × 11–14.6 mm [including wings], three-winged, glabrescent, brown when mature, dehiscing at the basal portion; wings unequal, larger one 5–7 × 6–7 mm, apex obtuse to rounded, smaller ones 5.8–7 × 0.6–1.6 mm. Seeds ca. 0.3 mm long, oblong.
"""
test_description_2 = """
Monoecious herb. Stem 15–40 cm tall, unbranched, glabrous. Leaves typically 3–5; blade slightly succulent, never coriaceous, subsymmetric, narrowly reniform, reniform or reniform-orbicular, 5–11 × 5–11 cm, margin shortly triangular–lobed, dentate, upper surface usually matt green above with greyish white veins but occasionally concolorous matt green throughout, sparsely to moderately pubescent, lower surface concolorous green or with green veins and reddish tinged intervenal lamina, sparsely to moderately pubescent along veins, and intervenal regions glabrous. Inflorescences solitary to many; peduncle 10–45 cm long. Male flowers: tepals usually pink, rarely white, outer pair usually elliptic to broadly elliptic, occasionally orbicular, ovateelliptic or obovate, 1.5–2.3 × 1.5–2.5 cm, inner pair obovate to spatulate, 2–2.8 × 1.6–1.9 cm. u>Female flowers/u>: tepals same colour as males, outer two elliptic to elliptic-obovate, inner three obovate to spatulate, subequal, 1.3–1.5 × 0.7–0.9 cm; ovary unequally 3-winged with one wing longer than the other two; 3-locular, styles 3.
"""
# Make client
client = Client(host = 'http://localhost:11434')

# Create model with reduced temperature if not already set-up
if True not in (model["name"].startswith("desc2matrix") for model in client.list()["models"]):
    print("ffa")
    client.create(model = 'desc2matrix', modelfile = modelfile)

# Loop over pages and pass to LLM for examination:
response = client.chat(model = 'desc2matrix',
                       messages = [{
                           'role': 'user',
                           'content': "{}\n{}\nSpecies name: Species 1\nDescription: {}\nSpecies name: Species 2\nDescription: {}".format(system_prompt, prompt, test_description_1, test_description_2)
                       }])

print(response["message"]["content"])