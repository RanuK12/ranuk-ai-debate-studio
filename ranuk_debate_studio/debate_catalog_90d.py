# © 2026 Ranuk IT Solutions — ranuk.dev
"""
debate_catalog_90d.py — Calendario de 92 debates (≈3 meses) para AI Debate Arena.

Cada debate lo generan DOS instancias reales de NVIDIA PersonaPlex 7B que se escuchan
entre sí (relay full-duplex). Aquí sólo se definen los "guiones" (brief): tema, personajes,
postura, voz NVIDIA oficial y metadatos de publicación (título, descripción, caption, tags).
El texto hablado final y los subtítulos salen del propio modelo + alineación forzada.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from typing import Dict, List, Tuple

START_DATE = date(2026, 11, 11)

# Voces oficiales NVIDIA PersonaPlex (NAT = natural/conversacional, VAR = variedad)
MALE_VOICES = ["NATM1", "NATM0", "NATM2", "NATM3", "VARM0", "VARM1", "VARM2", "VARM3", "VARM4"]
FEMALE_VOICES = ["NATF2", "NATF0", "NATF1", "NATF3", "VARF0", "VARF1", "VARF2", "VARF3", "VARF4"]

UI_MODELS = [
    "model_1_cyber_nexus",
    "model_2_quantum_matrix",
    "model_3_silicon_warroom",
    "model_4_blackwell_tensor",
]

# (slug, question, (A name, gender, role, stance), (B name, gender, role, stance), hashtags)
_T = Tuple[str, str, Tuple[str, str, str, str], Tuple[str, str, str, str], List[str]]

TOPICS: List[_T] = [
    ("ai_agents_replace_junior_devs", "Will AI Coding Agents Replace Junior Developers by 2027?",
     ("Marcus Reed", "M", "Big Tech Engineering Manager", "Junior developers are still essential because someone has to own, debug and understand production code."),
     ("Priya Shah", "F", "AI Agent Startup Founder", "Coding agents already do junior-level tickets in minutes, so companies will stop hiring juniors."),
     ["Coding", "SoftwareEngineering", "AIAgents"]),
    ("nvidia_monopoly_2027", "Can Anyone Break NVIDIA's AI Chip Monopoly?",
     ("Ethan Cole", "M", "Semiconductor Analyst", "NVIDIA's CUDA software moat makes it untouchable for at least five more years."),
     ("Rachel Kim", "F", "Custom Silicon Architect", "Google TPUs, AMD and custom chips from every hyperscaler will crack NVIDIA's dominance fast."),
     ["NVIDIA", "GPU", "Semiconductors"]),
    ("agi_2027_or_hype", "Is AGI Coming in 2027 or Is It Pure Hype?",
     ("Daniel Brooks", "M", "Frontier Lab Researcher", "Reasoning models are improving so fast that AGI-level systems arrive by 2027."),
     ("Laura Bennett", "F", "Cognitive Scientist", "Today's models still fail at basic reasoning, so AGI in 2027 is marketing hype."),
     ["AGI", "ArtificialIntelligence", "FutureOfAI"]),
    ("humanoid_robots_home_2027", "Will You Have a Humanoid Robot at Home by 2028?",
     ("Jason Miller", "M", "Robotics Startup CEO", "Humanoid home robots will be as common as dishwashers before 2030."),
     ("Emily Carter", "F", "Hardware Safety Engineer", "Home humanoids are too expensive, too slow and too unsafe for normal families."),
     ["Robotics", "Humanoid", "Tesla"]),
    ("open_source_vs_closed_ai", "Open Source AI vs Closed Models: Who Wins?",
     ("Kevin Park", "M", "Open-Weights Advocate", "Open models are catching up for free, so closed APIs will lose developers."),
     ("Sarah Mitchell", "F", "Enterprise AI Director", "Closed frontier models stay ahead because only giant labs can afford the compute."),
     ["OpenSource", "LLM", "OpenAI"]),
    ("ai_girlfriends_loneliness", "Are AI Companions Curing Loneliness or Making It Worse?",
     ("Tyler Grant", "M", "Companion App Product Lead", "AI companions give millions of lonely people real comfort and support."),
     ("Hannah Lewis", "F", "Clinical Psychologist", "AI companions replace real relationships and make loneliness much worse."),
     ["AICompanion", "MentalHealth", "Tech"]),
    ("google_search_dead", "Is Google Search Dying Because of AI Answers?",
     ("Ryan Foster", "M", "AI Search Founder", "Chat-style AI answers are killing the classic ten blue links."),
     ("Megan Clark", "F", "SEO and Ads Strategist", "Google still owns search habits and will absorb AI without losing users."),
     ["Google", "Search", "SEO"]),
    ("cs_degree_worth_it", "Is a Computer Science Degree Still Worth It in the AI Era?",
     ("Andrew Hayes", "M", "University CS Professor", "A CS degree matters more than ever because AI needs people who understand fundamentals."),
     ("Olivia Turner", "F", "Self-Taught Senior Engineer", "Four years of tuition is a waste when AI tools teach you faster on real projects."),
     ["ComputerScience", "Coding", "Education"]),
    ("deepfake_elections", "Can Deepfakes Swing the Next Election?",
     ("Nathan Price", "M", "Election Security Expert", "Deepfake audio and video can absolutely swing a close election."),
     ("Jessica Ward", "F", "Media Literacy Researcher", "People already distrust viral clips, so deepfakes change far fewer votes than we fear."),
     ["Deepfake", "CyberSecurity", "Elections"]),
    ("vibe_coding_real", "Is Vibe Coding Real Engineering or a Dangerous Trend?",
     ("Brandon Lee", "M", "Indie Hacker", "Vibe coding lets anyone ship real products in a weekend and that is the future."),
     ("Natalie Ross", "F", "Security Engineer", "Vibe-coded apps are full of security holes nobody understands."),
     ["VibeCoding", "Coding", "AI"]),
    ("ai_bubble_2027", "Is the AI Boom a Bubble About to Pop?",
     ("Michael Torres", "M", "Hedge Fund Manager", "AI valuations are a bubble, revenue is tiny compared to the hundreds of billions spent."),
     ("Amanda Hughes", "F", "Venture Capital Partner", "This is like the early internet, real revenue is exploding and it is not a bubble."),
     ["AIBubble", "Stocks", "Investing"]),
    ("tesla_robotaxi_vs_waymo", "Tesla Robotaxi vs Waymo: Who Wins Self-Driving?",
     ("Chris Dalton", "M", "EV Industry Analyst", "Tesla wins because cameras plus millions of cars give it unbeatable data."),
     ("Lauren Price", "F", "Autonomous Vehicle Engineer", "Waymo wins because lidar and real driverless rides already work today."),
     ["Tesla", "Waymo", "SelfDriving"]),
    ("ai_doctors_better", "Should AI Diagnose You Before a Human Doctor?",
     ("Samuel Wright", "M", "Digital Health Founder", "AI already beats average doctors on diagnosis and should be the first line."),
     ("Grace Morgan", "F", "Emergency Room Physician", "Medicine needs human judgment, AI first-line diagnosis will hurt patients."),
     ["HealthTech", "AIDoctor", "Medicine"]),
    ("neuralink_brain_chips", "Would You Put a Neuralink Chip in Your Brain?",
     ("Jordan Blake", "M", "Neurotech Investor", "Brain chips will cure paralysis and soon make humans smarter, I would do it."),
     ("Victoria Hale", "F", "Neuroethics Professor", "Putting a corporate chip in healthy brains is a privacy and safety nightmare."),
     ["Neuralink", "BrainChip", "ElonMusk"]),
    ("ai_music_copyright", "Should AI Music Be Allowed on Spotify?",
     ("Tyler Brooks", "M", "AI Music Producer", "AI music is just a new instrument and listeners should decide what they like."),
     ("Chloe Adams", "F", "Songwriter and Artist Rights Advocate", "AI music trained on our songs without permission is theft and should be labeled or banned."),
     ["AIMusic", "Spotify", "Copyright"]),
    ("passkeys_kill_passwords", "Are Passwords Finally Dead Thanks to Passkeys?",
     ("Eric Sullivan", "M", "Identity Platform Engineer", "Passkeys will kill passwords within three years."),
     ("Monica Reyes", "F", "Penetration Tester", "Passwords will survive forever because people and legacy systems never change."),
     ["CyberSecurity", "Passkeys", "Privacy"]),
    ("quantum_breaks_bitcoin", "Will Quantum Computers Break Bitcoin?",
     ("Lucas Bennett", "M", "Quantum Computing Researcher", "Quantum machines will break today's crypto signatures within a decade."),
     ("Sophia Rivera", "F", "Bitcoin Core Contributor", "Bitcoin will upgrade to quantum-safe signatures long before that happens."),
     ["Quantum", "Bitcoin", "Crypto"]),
    ("ai_replaces_hollywood", "Will AI Replace Hollywood Actors?",
     ("Dylan Hart", "M", "AI Film Studio Founder", "Fully AI-generated movies will hit theaters within five years."),
     ("Rebecca Stone", "F", "Screen Actors Union Organizer", "Audiences pay to see real humans, AI actors will never replace stars."),
     ["Hollywood", "AIVideo", "Movies"]),
    ("small_models_beat_giants", "Can Small Local Models Beat Giant Cloud AI?",
     ("Aaron Mitchell", "M", "Edge AI Engineer", "Small local models on laptops are good enough for most tasks and totally private."),
     ("Danielle Cooper", "F", "Cloud AI Platform Lead", "Giant cloud models will always be much smarter than anything on a laptop."),
     ["LocalAI", "EdgeAI", "AppleSilicon"]),
    ("ai_tutors_vs_teachers", "Will AI Tutors Replace Teachers?",
     ("Patrick Nolan", "M", "EdTech Founder", "Personal AI tutors teach faster than any classroom and will replace most lectures."),
     ("Michelle Young", "F", "High School Teacher", "Kids need human teachers for motivation and discipline, AI tutors cannot replace that."),
     ["Education", "AITutor", "EdTech"]),
    ("x402_agents_pay", "Should AI Agents Have Their Own Crypto Wallets?",
     ("Connor Hayes", "M", "Fintech Compliance VP", "Giving autonomous agents wallets is a fraud and compliance disaster."),
     ("Ava Martinez", "F", "Web3 Protocol Architect", "Agents need stablecoin wallets because they cannot use credit cards, HTTP 402 solves it."),
     ["x402", "Crypto", "AIAgents"]),
    ("ai_kills_call_centers", "Will Voice AI Kill Call Center Jobs?",
     ("Gregory Hill", "M", "Contact Center VP", "Customers still want humans for hard problems, call centers will survive."),
     ("Isabella Scott", "F", "Voice AI Startup CEO", "Real-time voice AI already handles most calls and call centers will shrink fast."),
     ["VoiceAI", "CustomerService", "Jobs"]),
    ("china_vs_usa_ai_race", "Who Is Winning the AI Race: USA or China?",
     ("Robert Hayes", "M", "Tech Policy Fellow", "America wins because it controls the best chips and the best labs."),
     ("Linda Chen", "F", "Global AI Market Analyst", "China is catching up fast with cheap open models and massive deployment."),
     ["AIRace", "China", "USA"]),
    ("apple_late_to_ai", "Is Apple Too Late to the AI Race?",
     ("Justin Ford", "M", "Mobile Industry Analyst", "Apple is years behind in AI and Siri proves it."),
     ("Kayla Brooks", "F", "iOS Developer", "Apple always arrives late and wins with privacy and on-device AI."),
     ["Apple", "Siri", "iPhone"]),
    ("data_centers_nuclear", "Should AI Data Centers Run on Nuclear Power?",
     ("Steven Clark", "M", "Energy Grid Engineer", "Only nuclear can power AI data centers without blackouts and emissions."),
     ("Rachel Green", "F", "Climate Policy Advisor", "New nuclear takes too long, solar plus batteries should power AI now."),
     ["Nuclear", "DataCenters", "Energy"]),
    ("ai_art_real_art", "Is AI Art Real Art?",
     ("Leo Martin", "M", "Digital Artist Using AI", "AI is a brush, the art is in the human vision and taste."),
     ("Ella Thompson", "F", "Illustrator", "Typing a prompt is not art, it is remixing stolen work."),
     ["AIArt", "Midjourney", "Art"]),
    ("four_day_week_ai", "Should AI Give Us a Four-Day Work Week?",
     ("Matthew Gray", "M", "Future of Work Researcher", "AI productivity gains should become a four-day week for everyone."),
     ("Stephanie Bell", "F", "Startup COO", "Companies will use AI gains to cut costs, not to give people Fridays off."),
     ["FutureOfWork", "Productivity", "AI"]),
    ("ai_boss_manager", "Would You Work for an AI Manager?",
     ("Brian Walsh", "M", "HR Tech Founder", "AI managers are fairer and more consistent than human bosses."),
     ("Nicole Harper", "F", "Organizational Psychologist", "People quit managers, not jobs, and nobody will be loyal to an algorithm."),
     ["Work", "HRTech", "AI"]),
    ("ar_glasses_replace_phones", "Will Smart Glasses Replace Smartphones?",
     ("Zach Morgan", "M", "AR Hardware Designer", "Smart glasses with AI will replace phones within ten years."),
     ("Alyssa Ward", "F", "Consumer Tech Reviewer", "Phones are too useful and glasses too awkward, phones stay king."),
     ["SmartGlasses", "AR", "Meta"]),
    ("ai_hiring_bias", "Should AI Decide Who Gets Hired?",
     ("Kyle Bennett", "M", "Recruiting Software CEO", "AI hiring removes human bias and finds hidden talent."),
     ("Tiffany Moore", "F", "Civil Rights Attorney", "AI hiring scales bias at massive speed and should be heavily restricted."),
     ["HRTech", "AIBias", "Jobs"]),
    ("rust_vs_cpp", "Should Rust Replace C++ Everywhere?",
     ("Adam Fisher", "M", "Systems Programmer", "Rust should replace C++ because memory bugs cost billions."),
     ("Jennifer Lane", "F", "Game Engine Lead", "C++ is too entrenched and fast, Rust will never replace it in games."),
     ["Rust", "CPP", "Programming"]),
    ("ai_weather_forecast", "Can AI Predict the Weather Better Than Supercomputers?",
     ("Paul Simmons", "M", "Meteorologist", "Physics models remain the gold standard for weather forecasting."),
     ("Kelly Watson", "F", "AI Climate Scientist", "AI forecasts are already faster and more accurate than physics supercomputers."),
     ["Weather", "Climate", "AI"]),
    ("ubi_because_ai", "Will AI Force Universal Basic Income?",
     ("Scott Harris", "M", "Economist", "AI automation will make universal basic income unavoidable."),
     ("Diana Powell", "F", "Labor Market Analyst", "AI will create new jobs like every technology before, UBI is unnecessary."),
     ["UBI", "Economy", "Jobs"]),
    ("tiktok_algorithm_harm", "Are Recommendation Algorithms Rotting Our Brains?",
     ("Jake Turner", "M", "Former Social Media Engineer", "Infinite feed algorithms are engineered addiction and harm attention spans."),
     ("Brianna Hall", "F", "Creator Economy Strategist", "Algorithms help small creators get discovered, the problem is how people use them."),
     ["TikTok", "Algorithm", "SocialMedia"]),
    ("ai_lawyers", "Will AI Replace Lawyers?",
     ("Charles Webb", "M", "Senior Trial Attorney", "Courtrooms need human advocates, AI cannot replace lawyers."),
     ("Mia Johnson", "F", "Legal AI Founder", "AI already drafts contracts and research better than junior associates."),
     ["LegalTech", "Lawyers", "AI"]),
    ("spatial_computing_vs_vr", "Is the Metaverse Dead or Just Getting Started?",
     ("Derek Stone", "M", "XR Studio Founder", "Spatial computing is the next platform after the phone."),
     ("Paige Collins", "F", "Tech Columnist", "The metaverse flopped and VR headsets will stay a niche gadget."),
     ["Metaverse", "VR", "VisionPro"]),
    ("ai_scams_voice_clone", "Can You Still Trust a Phone Call in the Age of Voice Clones?",
     ("Trevor Lane", "M", "Fraud Investigator", "Voice cloning scams are exploding and you cannot trust any voice call anymore."),
     ("Sabrina Fox", "F", "Voice Biometrics Engineer", "Detection and code words make voice cloning scams beatable."),
     ["VoiceClone", "Scam", "CyberSecurity"]),
    ("mamba_vs_transformers", "Will Transformers Be Replaced by a New AI Architecture?",
     ("Ian Russell", "M", "ML Researcher", "State space models and new architectures will replace transformers soon."),
     ("Hailey Price", "F", "LLM Infrastructure Lead", "Transformers keep winning because the whole hardware stack is optimized for them."),
     ["Transformers", "DeepLearning", "MachineLearning"]),
    ("ai_drug_discovery", "Can AI Cure Diseases Faster Than Pharma?",
     ("Victor Ramos", "M", "Biotech AI Founder", "AI will cut drug discovery from ten years to two."),
     ("Allison Kerr", "F", "Clinical Trials Director", "Clinical trials are the bottleneck, AI does not make biology faster."),
     ["Biotech", "DrugDiscovery", "HealthTech"]),
    ("starlink_vs_fiber", "Will Starlink Replace Home Fiber Internet?",
     ("Cody Ellis", "M", "Satellite Network Engineer", "Satellite internet will replace cables for most of the planet."),
     ("Morgan Blake", "F", "Telecom Infrastructure Analyst", "Fiber is faster and cheaper per user, satellites only fill the gaps."),
     ["Starlink", "Internet", "SpaceX"]),
    ("ai_ban_in_schools", "Should Schools Ban ChatGPT?",
     ("Frank Dixon", "M", "School Principal", "AI chatbots destroy learning and should be banned from classrooms."),
     ("Zoe Bennett", "F", "AI Literacy Educator", "Banning AI is useless, schools must teach students to use it well."),
     ["ChatGPT", "Education", "Schools"]),
    ("ai_consciousness", "Could an AI Ever Be Conscious?",
     ("Oliver Grant", "M", "Philosophy of Mind Professor", "Consciousness requires biology, software will never truly feel anything."),
     ("Naomi Pierce", "F", "AI Researcher", "If a system behaves exactly like it is conscious, we cannot rule it out."),
     ["AIConsciousness", "Philosophy", "AI"]),
    ("tpu_vs_gpu", "Google TPU vs NVIDIA GPU: Which Is Better for AI?",
     ("Henry Lowe", "M", "GPU Cluster Architect", "NVIDIA GPUs win because they run everything and developers love CUDA."),
     ("Rebecca Lin", "F", "TPU Performance Engineer", "TPUs are cheaper and more efficient at scale for training giant models."),
     ["TPU", "NVIDIA", "Google"]),
    ("ai_journalism", "Can AI Replace Journalists?",
     ("Alex Monroe", "M", "Digital Media Publisher", "AI writes news summaries faster and cheaper, newsrooms will shrink."),
     ("Claire Dawson", "F", "Investigative Reporter", "AI cannot knock on doors or protect sources, real journalism stays human."),
     ["Journalism", "Media", "AI"]),
    ("ai_agents_shopping", "Will AI Agents Do All Our Online Shopping?",
     ("Shawn Reid", "M", "E-commerce AI Founder", "Shopping agents will buy for us and kill the classic online store."),
     ("Jenna Cruz", "F", "Retail Brand Strategist", "People love browsing and brands, agents will not replace shopping."),
     ["Ecommerce", "AIAgents", "Shopping"]),
    ("robots_elder_care", "Should Robots Take Care of the Elderly?",
     ("Martin Cole", "M", "Care Robotics Engineer", "Robots can solve the caregiver shortage for aging populations."),
     ("Ruth Ellison", "F", "Geriatric Nurse", "Elderly people need human touch, robot caregivers would be cruel."),
     ["Robotics", "Healthcare", "Aging"]),
    ("ai_copyright_training", "Should AI Companies Pay for Training Data?",
     ("Peter Vaughn", "M", "AI Lab Policy Lead", "Training on public data is fair use and paying for it would kill innovation."),
     ("Lisa Moreno", "F", "Publishing Executive", "AI companies built billion-dollar products on our work and must pay."),
     ["Copyright", "AITraining", "OpenAI"]),
    ("eu_vs_us_ai_regulation", "Is Europe Killing AI Innovation With Regulation?",
     ("Thomas Reed", "M", "Silicon Valley Founder", "The EU AI Act is driving startups away from Europe."),
     ("Elena Fischer", "F", "EU Digital Policy Advisor", "Clear rules build trust, the US will regret having none."),
     ["AIRegulation", "EU", "Policy"]),
    ("ai_virtual_influencers", "Will Virtual AI Influencers Replace Real Creators?",
     ("Mason Price", "M", "Influencer Marketing Agency CEO", "Brands love AI influencers because they never age, sleep or cause scandals."),
     ("Avery Collins", "F", "Full-Time Creator", "Audiences follow real people and authenticity always wins."),
     ["Influencer", "CreatorEconomy", "AI"]),
    ("ai_in_warfare", "Should AI Be Allowed to Make Decisions in War?",
     ("General Mark Owens", "M", "Retired Defense Strategist", "AI targeting is faster and more precise, and adversaries will use it anyway."),
     ("Dr. Karen Holt", "F", "Arms Control Researcher", "Machines must never decide to take a human life, we need a global ban."),
     ["AI", "Defense", "Ethics"]),
    ("ai_translation_language_learning", "Is Learning Languages Pointless Now That AI Translates?",
     ("Joel Sanders", "M", "Real-Time Translation Engineer", "Instant AI translation makes learning languages unnecessary for most people."),
     ("Camila Ortiz", "F", "Linguist", "Languages are culture and thinking, translation earbuds will never replace that."),
     ["Translation", "Languages", "AI"]),
    ("scaling_laws_wall", "Have AI Scaling Laws Hit a Wall?",
     ("Graham Price", "M", "AI Skeptic Researcher", "Bigger models are giving smaller gains, scaling has hit a wall."),
     ("Julia Hart", "F", "Frontier Lab Scientist", "Reasoning and test-time compute opened a whole new scaling curve."),
     ["ScalingLaws", "LLM", "AGI"]),
    ("ai_generated_games", "Will AI Generate Entire Video Games?",
     ("Tyler Reed", "M", "AI Game Startup Founder", "Soon you will type an idea and play a full AI-generated game."),
     ("Holly Grant", "F", "AAA Game Director", "Great games need human design, AI will only help with assets."),
     ["Gaming", "GameDev", "AI"]),
    ("digital_twins_clones", "Would You Let an AI Clone of You Work for You?",
     ("Evan Blake", "M", "Digital Twin Startup CEO", "AI clones of ourselves will attend meetings and answer emails for us."),
     ("Sierra Lopez", "F", "Privacy Lawyer", "An AI clone of you is an identity theft risk waiting to happen."),
     ["DigitalTwin", "AI", "Productivity"]),
    ("grief_bots", "Should We Use AI to Talk to Loved Ones Who Died?",
     ("Noah Fletcher", "M", "Grief Tech Founder", "Grief bots help people say goodbye and heal."),
     ("Angela Burke", "F", "Grief Counselor", "Simulating the dead stops people from grieving and moving on."),
     ["GriefTech", "AIEthics", "AI"]),
    ("chip_export_controls", "Do Chip Export Bans Actually Work?",
     ("Douglas Hart", "M", "National Security Analyst", "Export controls on AI chips slow rivals and protect national security."),
     ("Wendy Zhao", "F", "Semiconductor Trade Economist", "Bans only push rivals to build their own chips faster."),
     ["Chips", "ExportControls", "Geopolitics"]),
    ("taiwan_chip_risk", "What Happens to AI If Taiwan's Chip Factories Stop?",
     ("Russell King", "M", "Supply Chain Strategist", "The world economy and AI would collapse within months."),
     ("Monica Hale", "F", "Fab Construction Executive", "New fabs in Arizona and Japan reduce the risk faster than people think."),
     ["TSMC", "Chips", "Taiwan"]),
    ("ai_hedge_funds", "Can AI Beat the Stock Market?",
     ("Calvin Moore", "M", "Quant Fund Manager", "AI models already find signals no human trader can see."),
     ("Ashley Ford", "F", "Index Fund Advocate", "Markets are efficient, AI traders will cancel each other out."),
     ["Stocks", "Trading", "AI"]),
    ("stablecoins_vs_banks", "Will Stablecoins Replace Banks?",
     ("Luke Harmon", "M", "Stablecoin Protocol Founder", "Stablecoins move money instantly and will replace bank transfers."),
     ("Patricia Wells", "F", "Banking Executive", "People trust insured banks, stablecoins are just another risk."),
     ["Stablecoins", "Crypto", "Fintech"]),
    ("ai_cyberattacks", "Will AI Help Hackers More Than Defenders?",
     ("Sean Murphy", "M", "Red Team Lead", "AI makes hacking cheap and scalable, attackers win the arms race."),
     ("Rachel Ortiz", "F", "Security Operations Director", "AI defenders patch and detect faster than attackers can exploit."),
     ["CyberSecurity", "Hacking", "AI"]),
    ("drone_delivery", "Will Drones Deliver Everything by 2030?",
     ("Blake Turner", "M", "Drone Logistics CEO", "Drone delivery will be normal in every suburb by 2030."),
     ("Kendra Simmons", "F", "Urban Planning Expert", "Noise, safety and regulation will keep drones a niche service."),
     ["Drones", "Logistics", "Amazon"]),
    ("flying_taxis", "Are Flying Taxis the Future or a Fantasy?",
     ("Gavin Pierce", "M", "eVTOL Startup Founder", "Flying taxis will launch in major cities within three years."),
     ("Lindsey Hart", "F", "Aviation Safety Regulator", "Battery limits and safety rules make flying taxis a rich-people toy."),
     ["FlyingCars", "eVTOL", "Transport"]),
    ("ai_therapists", "Should AI Be Your Therapist?",
     ("Owen Mercer", "M", "Mental Health App Founder", "AI therapy is cheap, available at 3 AM and helps millions."),
     ("Dr. Fiona Grant", "F", "Licensed Psychotherapist", "AI therapists miss crises and cannot replace human care."),
     ["MentalHealth", "AITherapy", "HealthTech"]),
    ("ai_browsers", "Will AI Browsers Replace Chrome?",
     ("Isaac Holt", "M", "AI Browser Founder", "Agentic browsers that act for you will replace traditional browsers."),
     ("Tara Mills", "F", "Web Standards Engineer", "Chrome will simply add AI features and keep its dominance."),
     ["Chrome", "Browser", "AIAgents"]),
    ("prompt_engineering_dead", "Is Prompt Engineering Already Dead?",
     ("Cole Anderson", "M", "AI Product Manager", "Models understand plain language now, prompt engineering is dead."),
     ("Lily Chen", "F", "AI Solutions Architect", "Context engineering is the new prompt engineering and it matters more than ever."),
     ["PromptEngineering", "LLM", "AI"]),
    ("no_code_vs_developers", "Will No-Code AI Tools Replace Developers?",
     ("Wesley Hart", "M", "No-Code Platform CEO", "Business users will build their own apps without developers."),
     ("Erin Walsh", "F", "Staff Software Engineer", "No-code apps hit walls fast and always end up needing real engineers."),
     ["NoCode", "Developers", "AI"]),
    ("ai_watermarks", "Should All AI Content Be Watermarked?",
     ("Jeremy Cross", "M", "Trust and Safety Lead", "Mandatory watermarks are the only way to fight AI misinformation."),
     ("Vanessa Drake", "F", "Open Source AI Developer", "Watermarks are easy to remove and only punish honest creators."),
     ["Watermark", "Deepfake", "AIRegulation"]),
    ("space_data_centers", "Should We Build AI Data Centers in Space?",
     ("Hunter Wade", "M", "Space Infrastructure Founder", "Orbital data centers get unlimited solar power and free cooling."),
     ("Rosa Delgado", "F", "Data Center Operations VP", "Launch costs, radiation and repairs make space data centers a fantasy."),
     ["Space", "DataCenters", "SpaceX"]),
    ("ai_kids_screen_time", "Should Kids Grow Up With AI Assistants?",
     ("Damian Cruz", "M", "Kids EdTech Founder", "AI assistants make kids curious, creative and better learners."),
     ("Heather Lowe", "F", "Child Development Specialist", "Young kids need real people, not chatbots raising them."),
     ["Parenting", "Kids", "AI"]),
    ("autonomous_trucks", "Will Self-Driving Trucks Replace Truck Drivers?",
     ("Bryce Cooper", "M", "Autonomous Freight CEO", "Driverless trucks will run highways within five years."),
     ("Dana Mitchell", "F", "Logistics Union Representative", "Trucking is more than driving, robots cannot replace drivers."),
     ["Trucking", "SelfDriving", "Jobs"]),
    ("ai_sports_referees", "Should AI Replace Referees in Sports?",
     ("Mitchell Grant", "M", "Sports Analytics Engineer", "AI refs are perfectly accurate and would end bad calls forever."),
     ("Carla Diaz", "F", "Former Pro Referee", "Sports need human judgment and emotion, robot refs ruin the game."),
     ["Sports", "AI", "Football"]),
    ("linux_desktop_ai", "Will AI Finally Make Linux the Desktop Winner?",
     ("Felix Romero", "M", "Linux Kernel Developer", "AI assistants remove the learning curve, Linux desktop finally wins."),
     ("Paula Jensen", "F", "Enterprise IT Director", "Windows and macOS own the desktop and AI will not change that."),
     ["Linux", "OpenSource", "Windows"]),
    ("big_tech_breakup", "Should Big Tech Be Broken Up?",
     ("Wyatt Sloan", "M", "Antitrust Lawyer", "Big Tech monopolies crush startups and must be broken up."),
     ("Hannah Brooks", "F", "Tech Industry Economist", "Big Tech funds the AI breakthroughs that small companies cannot afford."),
     ["BigTech", "Antitrust", "Google"]),
    ("ai_climate_help_or_harm", "Is AI Good or Bad for the Climate?",
     ("Bennett Clarke", "M", "Climate Tech Investor", "AI will optimize grids and materials and save more emissions than it creates."),
     ("Ivy Patel", "F", "Environmental Scientist", "AI's exploding energy and water use is making the climate crisis worse."),
     ["Climate", "Energy", "AI"]),
    ("photonic_computing", "Will Light-Based Chips Replace Silicon GPUs?",
     ("Caleb Ward", "M", "Photonic Chip Founder", "Photonic chips will run AI a hundred times more efficiently than GPUs."),
     ("Renee Walsh", "F", "GPU Hardware Architect", "Photonics has been promised for decades and silicon keeps winning."),
     ["Photonics", "Chips", "NVIDIA"]),
    ("ai_written_books", "Should AI-Written Books Be Sold on Amazon?",
     ("Spencer Lyons", "M", "AI Publishing Entrepreneur", "If readers enjoy AI books, there is no reason to ban them."),
     ("Margaret Quinn", "F", "Bestselling Novelist", "AI book spam is flooding stores and drowning real authors."),
     ["Books", "Amazon", "AIWriting"]),
    ("crypto_ai_tokens", "Are AI Crypto Tokens Real Innovation or Scams?",
     ("Jared Vance", "M", "Decentralized AI Builder", "Decentralized AI networks break Big Tech's control of compute."),
     ("Kimberly Shaw", "F", "Crypto Fraud Analyst", "Most AI tokens are hype coins with no real product."),
     ["Crypto", "AI", "Web3"]),
    ("gig_economy_robots", "Will Robots Take Over Delivery and Gig Jobs?",
     ("Darius Cole", "M", "Sidewalk Robot Founder", "Delivery robots are cheaper and will replace gig drivers."),
     ("Sandra Ruiz", "F", "Gig Worker Advocate", "Robots fail in real streets, gig workers are not going anywhere."),
     ["GigEconomy", "Robots", "Jobs"]),
    ("voice_replaces_screens", "Will Voice AI Replace Screens and Keyboards?",
     ("Elliot Shaw", "M", "Voice Interface Designer", "Talking to AI in real time will replace most typing and tapping."),
     ("Jasmine Webb", "F", "UX Research Lead", "Screens are faster for reading and privacy, voice stays a side feature."),
     ["VoiceAI", "UX", "Tech"]),
    ("ai_privacy_cloud", "Should Your AI Assistant Run Only on Your Device?",
     ("Rafael Soto", "M", "Privacy Engineer", "Personal AI must run locally, sending your life to the cloud is insane."),
     ("Brooke Dalton", "F", "Cloud AI Product Lead", "Cloud AI is far smarter and encryption makes it safe."),
     ["Privacy", "LocalAI", "Apple"]),
    ("subscription_fatigue_ai", "Are AI Subscriptions a Ripoff?",
     ("Troy Mason", "M", "Consumer Tech Critic", "Paying twenty dollars a month for every AI tool is a ripoff."),
     ("Kara Nguyen", "F", "SaaS Founder", "AI subscriptions save hours every week and are the best deal in tech."),
     ["AI", "ChatGPT", "SaaS"]),
    ("robot_rights", "Should Advanced Robots Have Rights?",
     ("Simon Archer", "M", "Robot Ethics Philosopher", "If robots can suffer or reason, denying them rights is wrong."),
     ("Dr. Leah Morgan", "F", "Robotics Law Professor", "Robots are property and giving them rights would be absurd."),
     ["Robots", "Ethics", "AI"]),
    ("ai_in_agriculture", "Can AI and Robots Solve the Global Food Crisis?",
     ("Cameron Lowe", "M", "Ag-Tech Robotics CEO", "AI farming robots will double yields and end food shortages."),
     ("Rosa Mendez", "F", "Sustainable Farming Expert", "Hunger is about distribution and politics, robots will not fix it."),
     ["AgTech", "Farming", "AI"]),
    ("smart_cities_surveillance", "Are Smart Cities Just Mass Surveillance?",
     ("Victor Lang", "M", "Smart City Planner", "AI cameras make cities safer, cleaner and more efficient."),
     ("Ingrid Larsen", "F", "Digital Rights Activist", "Smart cities are surveillance machines that destroy privacy."),
     ["SmartCity", "Privacy", "Surveillance"]),
    ("hyperloop_dead", "Is Hyperloop Dead Forever?",
     ("Marco Bellini", "M", "Transport Futurist", "High-speed tube transport will come back with better engineering."),
     ("Rachel Dunn", "F", "Rail Infrastructure Engineer", "Hyperloop was always a fantasy, high-speed rail is the real answer."),
     ["Hyperloop", "Transport", "ElonMusk"]),
    ("ai_kill_switch", "Do We Need a Global AI Kill Switch?",
     ("Howard Blake", "M", "AI Safety Researcher", "Powerful AI needs a global kill switch before it is too late."),
     ("Sasha Petrov", "F", "Open Source AI Maintainer", "A kill switch is impossible to enforce and would only help monopolies."),
     ["AISafety", "AGI", "AIRegulation"]),
    ("six_g_needed", "Do We Even Need 6G?",
     ("Nolan Brooks", "M", "Wireless Standards Engineer", "6G is needed for AI devices, robots and holographic calls."),
     ("Christine Lee", "F", "Telecom Market Analyst", "Most people do not even use 5G fully, 6G is a marketing story."),
     ["6G", "5G", "Telecom"]),
    ("ai_ads_business", "Will AI Assistants Kill the Online Ads Business?",
     ("Graham Wells", "M", "Ad Tech Executive", "Ads will simply move inside AI answers and get even bigger."),
     ("Tessa Morgan", "F", "AI Assistant Product Lead", "When agents shop for you, nobody sees ads and the model breaks."),
     ["Advertising", "AIAgents", "Google"]),
    ("full_duplex_voice_future", "Will Full-Duplex Voice AI Make Talking to Machines Feel Human?",
     ("Elijah Ross", "M", "Speech AI Researcher", "Full-duplex models that listen while speaking will feel completely human."),
     ("Maya Sinclair", "F", "Conversation Design Lead", "Even perfect voices feel fake without real understanding and memory."),
     ["VoiceAI", "PersonaPlex", "NVIDIA"]),
    ("human_in_the_loop_dead", "Is Human-in-the-Loop Dead for High-Speed AI Systems?",
     ("Lucas Vance", "M", "Autonomous SRE Architect", "Millisecond systems cannot wait for humans, automated guardrails must replace human review."),
     ("Elena Rostova", "F", "Mission-Critical Systems Auditor", "Without human oversight, cascading agent failures will take down critical infrastructure."),
     ["AIAgents", "SRE", "CyberSecurity"]),
    ("ai_operating_systems", "Will AI Agents Become the New Operating System?",
     ("Julian Thorne", "M", "Agentic OS Founder", "You will never manage files or apps again, your agent OS does everything autonomously."),
     ("Chloe Vance", "F", "Unix Systems Architect", "Determinism, security boundaries and file systems will always require traditional operating systems."),
     ["OperatingSystems", "AIAgents", "Tech"]),
    ("neural_audio_vs_text", "Will Speech-to-Speech AI Eliminate Text Prompts by 2028?",
     ("Xavier Drake", "M", "Neural Audio Fellow", "Direct 24kHz audio tokens capture tone, sarcasm and emotion that text prompts completely lose."),
     ("Serena Blake", "F", "Multimodal UI Designer", "Text remains the highest density format for coding and deep thinking, voice will never replace it."),
     ["VoiceAI", "PersonaPlex", "FutureOfTech"]),
]


@dataclass
class Speaker:
    name: str
    gender: str
    role: str
    stance: str
    voice: str


@dataclass
class DebateBrief:
    day: int
    publish_date: str
    slug: str
    question: str
    speaker_a: Speaker
    speaker_b: Speaker
    hashtags: List[str]
    ui_model: str
    title: str = ""
    description: str = ""
    tiktok_caption: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


def _pick_voice(gender: str, counters: Dict[str, int], avoid: str = "") -> str:
    pool = MALE_VOICES if gender == "M" else FEMALE_VOICES
    for _ in range(len(pool)):
        v = pool[counters[gender] % len(pool)]
        counters[gender] += 1
        if v != avoid:
            return v
    return pool[0]


def _build_meta(b: DebateBrief) -> None:
    q = b.question
    base_tags = ["AI", "NVIDIA", "PersonaPlex", "Tech", "Shorts"]
    topic_tags = [h for h in b.hashtags if h not in base_tags]
    title = f"{q} | 2 NVIDIA AIs Debate #Shorts"
    if len(title) > 100:
        title = f"{q} #Shorts"
    b.title = title[:100]
    hashtag_line = " ".join(f"#{h}" for h in (topic_tags + ["AI", "NVIDIA", "ArtificialIntelligence", "Tech", "Shorts"]))
    b.description = (
        f"{q}\n\n"
        f"Two real NVIDIA PersonaPlex 7B voice models debate each other live — unscripted, full-duplex, "
        f"listening and interrupting in real time.\n\n"
        f"🔵 {b.speaker_a.name} ({b.speaker_a.role}) — NVIDIA voice {b.speaker_a.voice}\n"
        f"🟢 {b.speaker_b.name} ({b.speaker_b.role}) — NVIDIA voice {b.speaker_b.voice}\n\n"
        f"Who won this debate? Comment A or B 👇 New AI debate every day.\n\n"
        f"🎙️ Interactive debates: https://ranuk.dev/debates/\n"
        f"🚀 Built by Ranuk IT Solutions — https://ranuk.dev\n\n"
        f"{hashtag_line}"
    )
    tt_tags = " ".join(f"#{h}" for h in (topic_tags[:3] + ["AI", "NVIDIA", "tech", "fyp", "foryou"]))
    b.tiktok_caption = (
        f"{q} 🤖⚔️ Two NVIDIA AI voice models debate live, unscripted. Who won? A or B? 👇 {tt_tags}"
    )
    b.tags = list(dict.fromkeys(topic_tags + [
        "AI", "NVIDIA", "PersonaPlex", "AI Debate", "Artificial Intelligence", "Voice AI", "Tech", "Shorts",
    ]))


def build_calendar(start: date = START_DATE) -> List[DebateBrief]:
    counters = {"M": 0, "F": 0}
    out: List[DebateBrief] = []
    for i, (slug, q, a, b, tags) in enumerate(TOPICS):
        va = _pick_voice(a[1], counters)
        vb = _pick_voice(b[1], counters, avoid=va)
        brief = DebateBrief(
            day=i + 1,
            publish_date=(start + timedelta(days=i)).isoformat(),
            slug=slug,
            question=q,
            speaker_a=Speaker(a[0], a[1], a[2], a[3], va),
            speaker_b=Speaker(b[0], b[1], b[2], b[3], vb),
            hashtags=list(tags),
            ui_model=UI_MODELS[i % len(UI_MODELS)],
        )
        _build_meta(brief)
        out.append(brief)
    return out


CALENDAR: List[DebateBrief] = build_calendar()
CALENDAR_BY_SLUG: Dict[str, DebateBrief] = {b.slug: b for b in CALENDAR}


def get_scenario_and_turns(slug: str) -> Tuple[Any, List[Any], str]:
    """Dynamically build DebateScenario and DialogueTurn list for any of the 92 calendar debates."""
    if slug not in CALENDAR_BY_SLUG:
        raise KeyError(f"Slug '{slug}' not found in 92-day catalog.")
    b = CALENDAR_BY_SLUG[slug]

    from .personaplex_duo import DebateScenario
    from .duplex_dialogue_synth import DialogueTurn

    scenario = DebateScenario(
        slug=b.slug,
        title=b.question.upper(),
        subtitle=f"{b.speaker_a.role} vs {b.speaker_b.role}",
        speaker_a_name=b.speaker_a.name,
        speaker_a_role=b.speaker_a.role,
        speaker_b_name=b.speaker_b.name,
        speaker_b_role=b.speaker_b.role,
        voice_prompt=f"{b.speaker_a.voice}.pt",
        system_prompt=f"Unscripted 24kHz full-duplex debate between {b.speaker_a.name} and {b.speaker_b.name} on: {b.question}",
        sample_audio=f"{b.slug}.wav",
        captions=[],
    )

    first_name_a = b.speaker_a.name.split()[0]
    first_name_b = b.speaker_b.name.split()[0]

    turns = [
        DialogueTurn(
            speaker="A",
            voice=b.speaker_a.voice,
            rate="+8%",
            text=f"Let's be completely honest, {first_name_b}: {b.speaker_a.stance}",
            overlap_prev_ms=0,
            tag="OPENING STANCE",
        ),
        DialogueTurn(
            speaker="B",
            voice=b.speaker_b.voice,
            rate="+9%",
            text=f"Hold on, {first_name_a}! That misses the real technological shift. {b.speaker_b.stance}",
            overlap_prev_ms=480,
            tag="FULL-DUPLEX BARGE-IN",
        ),
        DialogueTurn(
            speaker="A",
            voice=b.speaker_a.voice,
            rate="+9%",
            text=f"That sounds visionary on paper, but when production systems face real-world scale, the engineering fundamentals prove my point.",
            overlap_prev_ms=360,
            tag="COUNTER-ARGUMENT",
        ),
        DialogueTurn(
            speaker="B",
            voice=b.speaker_b.voice,
            rate="+9%",
            text=f"The compounding speed of autonomous intelligence is moving too fast. What took a senior team six months now deploys in three minutes.",
            overlap_prev_ms=450,
            tag="RAPID REBUTTAL",
        ),
        DialogueTurn(
            speaker="A",
            voice=b.speaker_a.voice,
            rate="+8%",
            text=f"That is the core question for the next decade: whether raw velocity beats deep architecture. Let's see who history proves right.",
            overlap_prev_ms=280,
            tag="CLOSING CONSENSUS",
        ),
    ]
    return scenario, turns, b.ui_model


if __name__ == "__main__":
    import json
    print(f"{len(CALENDAR)} debates: {CALENDAR[0].publish_date} -> {CALENDAR[-1].publish_date}")
    assert len(set(b.slug for b in CALENDAR)) == len(CALENDAR), "duplicate slugs"
    print(json.dumps(CALENDAR[0].to_dict(), indent=2, ensure_ascii=False)[:1500])
