# Category audit

Which rule matched which line, over the whole corpus.
Correct `data/category_rules.yaml` if a match looks wrong, then re-run.

## short_slot (corpus 19, sample 18, minimum 15)

- [S] `E01-L003` Edda Halloran (firm): I set it down an hour ago. -> slot 1.4s < 1.5s
- [ ] `E01-L012` Edda Halloran (hard): Family does not bring constables. -> slot 1.4s < 1.5s
- [S] `E01-L015` Edda Halloran (low): Say it once more. -> slot 1.4s < 1.5s
- [S] `E01-L021` Edda Halloran (ice): By your authority. Yes. -> slot 1.2s < 1.5s
- [S] `E01-L023` Edda Halloran (still): No. -> slot 1.2s < 1.5s
- [S] `E01-L030` Edda Halloran (not moving): Call it what you like. -> slot 1.2s < 1.5s
- [S] `E02-L004` Joss Marek (dry): Ticket burnt with the ship. -> slot 1.4s < 1.5s
- [S] `E02-L007` Joss Marek (tired): His head was full already. -> slot 1.4s < 1.5s
- [S] `E02-L011` Edda Halloran (raw): He wants the lamp. -> slot 1.4s < 1.5s
- [S] `E02-L013` Edda Halloran (quiet): That is the same thing. -> slot 1.4s < 1.5s
- [S] `E02-L025` Edda Halloran (shaken): ... how did you ... -> slot 1.2s < 1.5s
- [S] `E03-L008` Edda Halloran (still): He bought them. -> slot 1.2s < 1.5s
- [S] `E03-L017` Joss Marek (short): Your light is my work. -> slot 1.2s < 1.5s
- [S] `E03-L021` Edda Halloran (afraid of it): Not tonight. -> slot 1.4s < 1.5s
- [S] `E04-L015` Joss Marek (tired): I'll say it any way you need. -> slot 1.2s < 1.5s
- [S] `E04-L018` Edda Halloran (the name, first time): Joss — the coat. Whose? -> slot 1.4s < 1.5s
- [S] `E04-L021` Edda Halloran (flat): It isn't alone. -> slot 1.4s < 1.5s
- [S] `E04-L025` Edda Halloran (to it, gentle): That's enough. Go down. -> slot 1.4s < 1.5s
- [S] `E05-L016` Edda Halloran (cutting): Two years and still no. -> slot 1.4s < 1.5s

## chain_member (corpus 6, sample 6, minimum 3)

- [S] `E01-L024` Silas Vane (smiling): She always says no ... -> C01-001 (same-speaker)
- [S] `E01-L025` Silas Vane (same, leaning in): ... until the price is right. -> C01-001 (same-speaker)
- [S] `E01-L026` Halloran (Edda's father) (desperate): Edda, my girl, do not ... -> C01-002 (same-speaker)
- [S] `E01-L027` Halloran (Edda's father) (same, urgent): ... sign nothing tonight. -> C01-002 (same-speaker)
- [S] `E03-L030` Halloran (Edda's father) (same, urgent): Say it as a promise, not a ... -> C03-003 (interlocked)
- [S] `E03-L031` Edda Halloran (finishing it): ... a dare. I hear you, Father. -> C03-003 (interlocked)

## voice_or_offscreen (corpus 16, sample 13, minimum 5)

- [ ] `E01-L012` Edda Halloran (hard): Family does not bring constables. -> off-screen
- [S] `E01-L017` Joss Marek (off-screen): Tell that to the tide, Mistress. -> off-screen
- [ ] `E01-L031` Joss Marek (from the quay): Barge is clear. She means the paper, not the girl. -> voice-over
- [S] `E02-L006` Edda Halloran (accusing): So it is you filling his head. -> off-screen
- [S] `E02-L029` Joss Marek (later, from the quay): She has no idea what a signature costs. -> voice-over
- [S] `E02-L031` Joss Marek (off-screen, far): Lock the gate, Edda. It is you he means. -> off-screen
- [S] `E03-L014` Joss Marek (off-screen): Someone did. From the stair. -> off-screen
- [S] `E03-L023` Joss Marek (quiet, mostly to himself): She does not know she is being priced and not courted. -> voice-over
- [ ] `E03-L033` Joss Marek (at the stair, far): Marek's barge is at the gate if you want a witness. -> off-screen
- [S] `E04-L002` Voice of the lamp (V.O., a child): One, two, three, four — -> voice-over
- [S] `E04-L004` Joss Marek (off-screen): LIGHT THE STAIR! Somebody light the stair! -> off-screen
- [S] `E04-L006` Joss Marek (flat, calm, certain): Then he'll be wet and right, in that order. -> voice-over
- [S] `E04-L024` Voice of the lamp (V.O., a child): — nine, ten, eleven, twelve — -> voice-over
- [S] `E06-L008` Edda Halloran (from the lamp stair): On the charge of my father, then. -> off-screen
- [S] `E06-L021` Voice of the lamp (V.O., a child, one count only): — thirteen. -> voice-over
- [S] `E06-L023` Joss Marek (from the water, last line of the season): Light the stair, Edda. There's three boats coming home. -> voice-over

## address_shift (corpus 11, sample 10, minimum 10)

- [ ] `E01-L028` Edda Halloran (formal, a line newly drawn): You will leave my father's room, Mistress Caine. -> Mistress Caine: Mistress Caine
- [S] `E01-L029` Mistress Caine (cutting): Aunt. That is what you called me at Christmastide. -> Edda Halloran: Aunt. That is what you called me at Christmastide
- [S] `E02-L028` Edda Halloran (to her father, soft): Hush now, Father. I am here. -> Halloran (Edda's father): Hush now, Father
- [S] `E03-L002` Edda Halloran (controlled): I have an hour, Mistress Caine. -> Mistress Caine: Mistress Caine
- [S] `E03-L024` Edda Halloran (to the rain): Aunt would have said that nicer. -> Mistress Caine: Aunt would have said that nicer
- [S] `E03-L031` Edda Halloran (finishing it): ... a dare. I hear you, Father. -> Halloran (Edda's father): I hear you, Father
- [S] `E04-L018` Edda Halloran (the name, first time): Joss — the coat. Whose? -> Joss Marek: Joss — the coat
- [S] `E05-L014` Edda Halloran (in front of her father): Step off the stair, Silas Vane. -> Silas Vane: Step off the stair, Silas Vane
- [S] `E05-L019` Edda Halloran (fixed): In your harbour, Mistress Caine. -> Mistress Caine: Mistress Caine
- [S] `E05-L022` Edda Halloran (to the man she calls Father, then the man she calls Father): Father, hold on. Father Anselm, hold him. -> Brother Anselm: Father Anselm, hold him
- [S] `E06-L011` Edda Halloran (fixed, then soft): Aunt. You were always family. Just not kind. -> Mistress Caine: Aunt. You were always family

## threat_or_accusation (corpus 61, sample 31, minimum 10)

- [S] `E01-L005` Edda Halloran (cold): She always comes when I sleep. -> delivery: cold
- [ ] `E01-L010` Edda Halloran (flat): Then she can wait for the tide. -> delivery: flat
- [ ] `E01-L012` Edda Halloran (hard): Family does not bring constables. -> delivery: hard
- [ ] `E01-L013` Silas Vane (mock): Your father owed mine. You could still marry it off. -> delivery: mock
- [S] `E01-L014` Mistress Caine (businesslike): The debt is mine, the deed is mine, the winter is mine. -> delivery: businesslike
- [S] `E01-L015` Edda Halloran (low): Say it once more. -> delivery: low
- [ ] `E01-L016` Mistress Caine (unmoved): The lamp is mine by morning. -> delivery: unmoved
- [ ] `E01-L019` Edda Halloran (measured): He is the only one who answered a bell tonight. -> delivery: measured
- [ ] `E01-L020` Constable Roe (formal): By my authority — is this the keeper's daughter? -> delivery: formal
- [S] `E01-L021` Edda Halloran (ice): By your authority. Yes. -> delivery: ice
- [ ] `E01-L022` Mistress Caine (final): Sign by the turn of the glass, or I take the lamp tonight. -> \bor I take\b
- [ ] `E01-L028` Edda Halloran (formal, a line newly drawn): You will leave my father's room, Mistress Caine. -> delivery: formal
- [S] `E01-L029` Mistress Caine (cutting): Aunt. That is what you called me at Christmastide. -> delivery: cutting
- [ ] `E01-L031` Joss Marek (from the quay): Barge is clear. She means the paper, not the girl. -> \bshe means the paper\b
- [ ] `E02-L001` Constable Roe (official): Turn it out. All of it. -> delivery: official
- [S] `E02-L004` Joss Marek (dry): Ticket burnt with the ship. -> delivery: dry
- [ ] `E02-L005` Constable Roe (hard): Then you will answer for the ship as well as the lace. -> \banswer for\b
- [ ] `E02-L008` Edda Halloran (shifting): Constable. Search the house, not the man who feeds it. -> \bsearch the house\b
- [S] `E02-L009` Company clerk (Caine's man, grey coat) (pleased): Mistress Caine will hear of this. -> \bwill hear of this\b
- [S] `E02-L015` Brother Anselm (measured): Miss Halloran. The company offers charity for the keeper's winter. -> delivery: measured
- [S] `E02-L016` Edda Halloran (cold): Charity from Caine. -> delivery: cold
- [ ] `E02-L018` Edda Halloran (low, dangerous): Say that to him when he asks for bread. -> \bsay that to\b
- [ ] `E02-L019` Brother Anselm (warning): My child, do not make an enemy of a signature. -> delivery: warning
- [S] `E02-L020` Edda Halloran (flat): Father does not sign. That is the answer. -> delivery: flat
- [ ] `E02-L021` Edda Halloran (struggling): Give me the rope. -> \bgive me the rope\b
- [ ] `E02-L022` Joss Marek (already there): You will drop him. -> \byou will drop\b
- [ ] `E02-L023` Edda Halloran (furious): Mind your own water. -> \bmind your own\b
- [S] `E02-L029` Joss Marek (later, from the quay): She has no idea what a signature costs. -> \bwhat a .{0,30} costs\b
- [S] `E02-L031` Joss Marek (off-screen, far): Lock the gate, Edda. It is you he means. -> \bit is you he means\b
- [ ] `E03-L001` Mistress Caine (busy): Stand there until I finish. -> \bstand there\b
- [S] `E03-L003` Mistress Caine (dry): You have the tide. It is less. -> delivery: dry
- [ ] `E03-L007` Silas Vane (serious now): There is a letter here that says your father sold a ship's stores. -> \bsold a ship's stores\b
- [ ] `E03-L009` Silas Vane (enjoying it): Say that to the magistrate. -> \bmagistrate\b
- [S] `E03-L010` Edda Halloran (low): What do you want, Silas, out of a dead man's paper? -> delivery: low
- [S] `E03-L011` Silas Vane (final): Your name in my bed and my seal on that lamp. -> delivery: final
- [S] `E03-L012` Mistress Caine (sharp): You are not worth a seal. Take her away. -> \btake her away\b
- [ ] `E03-L013` Edda Halloran (shaking): I did not say it. -> \bdid not say it\b
- [S] `E03-L014` Joss Marek (off-screen): Someone did. From the stair. -> Someone did
- [S] `E03-L018` Edda Halloran (measured): Then tell me what a '61 inquiry letter costs a keeper's daughter. -> \binquiry letter\b
- [S] `E03-L023` Joss Marek (quiet, mostly to himself): She does not know she is being priced and not courted. -> \bbeing priced\b
- [S] `E03-L025` Halloran (Edda's father) (clear): You went to the house. My girl, why did you go? -> \bwhy did you go\b
- [S] `E03-L031` Edda Halloran (finishing it): ... a dare. I hear you, Father. -> \bI hear you\b
- [ ] `E03-L032` Edda Halloran (to the lamp): Not one more winter. Every winter they come for. -> \bnot one more\b
- [S] `E04-L006` Joss Marek (flat, calm, certain): Then he'll be wet and right, in that order. -> delivery: flat
- [ ] `E04-L010` Halloran (Edda's father) (instantly): You lie like your mother. -> \byou lie\b
- [S] `E04-L021` Edda Halloran (flat): It isn't alone. -> delivery: flat
- [ ] `E05-L001` Company clerk (shipping office, grey beard) (flat): Name of the vessel or nothing. -> delivery: flat
- [ ] `E05-L005` Company clerk (shipping office, grey beard) (below his voice): Mistress, there's a gentleman at the altar who does both. -> delivery: ice
- [S] `E05-L009` Edda Halloran (low): And Caine gives. -> delivery: low
- [S] `E05-L010` Brother Anselm (final): Caine gives, I keep your father breathing, and you keep silent. -> delivery: final
- [S] `E05-L011` Constable Roe (formal): Halloran. You will come with me for the sale of king's stores. -> delivery: formal
- [S] `E05-L014` Edda Halloran (in front of her father): Step off the stair, Silas Vane. -> \bstep off\b
- [S] `E05-L015` Silas Vane (mock-hurt): Still the betrothed? Two years and still— -> delivery: mock
- [S] `E05-L016` Edda Halloran (cutting): Two years and still no. -> delivery: cutting
- [ ] `E05-L018` Mistress Caine (arriving, cold): You will all be silent in my harbour. -> delivery: cold
- [ ] `E05-L020` Mistress Caine (to the constable only): Take the keeper. The girl can bring the paper. -> \bTake the keeper\b
- [S] `E05-L022` Edda Halloran (to the man she calls Father, then the man she calls Father): Father, hold on. Father Anselm, hold him. -> \bhold him\b
- [ ] `E05-L028` Joss Marek (flat): Caine's money is my money now, and has been nine months. -> delivery: flat
- [ ] `E06-L007` Constable Roe (dry, at last): On what charge, master? The lace is ticketed now. -> delivery: dry
- [ ] `E06-L014` Edda Halloran (unrepentant): I forgave the Christmastide. Not the paper. -> delivery: unrepentant
- [S] `E06-L019` Halloran (Edda's father) (below, on the stair, upright): Edda. Lass. I am standing on my own stair again, look at me. -> delivery: low

## tender_or_intimate (corpus 59, sample 34, minimum 10)

- [S] `E01-L001` Edda Halloran (steady): The lamp stays lit. -> \bthe lamp stays lit\b
- [S] `E01-L004` Halloran (Edda's father) (afraid): Caine came again while you slept. -> delivery: afraid
- [S] `E01-L006` Halloran (Edda's father) (pleading): Promise me you will not sign her paper. -> delivery: pleading
- [S] `E01-L007` Edda Halloran (careful): What paper? -> delivery: careful
- [ ] `E01-L008` Edda Halloran (quiet anger): Tell me what she wants with my father's name. -> delivery: quiet
- [ ] `E01-L009` Halloran (Edda's father) (broken): The lamp, Edda. Only the lamp. -> delivery: broken
- [ ] `E01-L018` Halloran (Edda's father) (frightened): The bargeman. He is trouble, Edda. -> delivery: frightened
- [S] `E01-L023` Edda Halloran (still): No. -> delivery: still
- [S] `E01-L026` Halloran (Edda's father) (desperate): Edda, my girl, do not ... -> \bmy girl\b
- [S] `E01-L030` Edda Halloran (not moving): Call it what you like. -> delivery: not moving
- [ ] `E01-L032` Edda Halloran (tender): The lamp stays lit, Father. Even if I burn for it. -> \beven if I burn\b
- [ ] `E02-L002` Joss Marek (patient): It is lace, sir. Bought with honest money. -> delivery: patient
- [S] `E02-L007` Joss Marek (tired): His head was full already. -> \bwas full already\b
- [S] `E02-L010` Delia (kind): Eat, love. He will want you standing. -> \beat, love\b
- [S] `E02-L012` Delia (careful): He wants your father off the rock before the spring. -> delivery: careful
- [S] `E02-L013` Edda Halloran (quiet): That is the same thing. -> delivery: quiet
- [ ] `E02-L024` Joss Marek (quiet): Hold the lamp. Do not speak. -> \bdo not speak\b
- [ ] `E02-L027` Halloran (Edda's father) (drifting): The girl will not sign it, Joss. She is all I have left. -> \ball I have left\b
- [S] `E02-L028` Edda Halloran (to her father, soft): Hush now, Father. I am here. -> \bhush now\b
- [ ] `E02-L032` Edda Halloran (not moving): Then he can knock. -> delivery: not moving
- [S] `E03-L008` Edda Halloran (still): He bought them. -> delivery: still
- [ ] `E03-L015` Joss Marek (not kind): You are stood in the rain over a man's handwriting. -> delivery: kind
- [ ] `E03-L019` Joss Marek (careful now): Everything. And nothing, if the buyer is honest. -> delivery: careful
- [S] `E03-L021` Edda Halloran (afraid of it): Not tonight. -> \bnot tonight\b
- [S] `E03-L023` Joss Marek (quiet, mostly to himself): She does not know she is being priced and not courted. -> delivery: quiet
- [S] `E03-L025` Halloran (Edda's father) (clear): You went to the house. My girl, why did you go? -> \bmy girl\b
- [ ] `E03-L026` Edda Halloran (small): You were dying quietly. -> delivery: small
- [ ] `E03-L028` Halloran (Edda's father) (tender): If they take the lamp, they take the ten years I put in it. -> delivery: tender
- [S] `E03-L029` Edda Halloran (breaking): I will not let them take it. -> delivery: breaking
- [S] `E03-L030` Halloran (Edda's father) (same, urgent): Say it as a promise, not a ... -> \bsay it as a promise\b
- [ ] `E04-L003` Edda Halloran (afraid): Not tonight. Please, not tonight. -> \bplease\b
- [S] `E04-L007` Edda Halloran (to the lamp, begging): Turn to him. Turn to him, he is my father's water. -> \bturn to him\b
- [ ] `E04-L012` Delia (fussed): Look at him, look at the floor he's made — -> delivery: fussed
- [S] `E04-L014` Halloran (Edda's father) (broken): Three on my shoal. Say it to me. -> delivery: broken
- [ ] `E04-L016` Edda Halloran (careful): You told him the count before you told me. -> delivery: careful
- [S] `E04-L017` Joss Marek (unashamed): He's the one who can't sleep after. -> \bwho can't sleep\b
- [ ] `E04-L020` Joss Marek (quieter): You keep this glass clean at midnight alone. -> delivery: quiet
- [S] `E04-L021` Edda Halloran (flat): It isn't alone. -> \bit isn't alone\b
- [S] `E04-L023` Edda Halloran (small): My father put me up here at nine and said count and don't stop. -> delivery: small
- [S] `E04-L025` Edda Halloran (to it, gentle): That's enough. Go down. -> delivery: gentle
- [ ] `E04-L026` Joss Marek (not asking): I'll count it with you when the glass turns. -> \bcount it with you\b
- [S] `E04-L027` Edda Halloran (tender, terrified): If you touch my father's lamp you'll be standing in it, not beside it. -> delivery: tender
- [ ] `E05-L002` Edda Halloran (patient): The trawler on the shoal, the fourth night. -> delivery: patient
- [ ] `E05-L004` Edda Halloran (careful): Then who insured it, and who paid the bargeman's lace? -> delivery: careful
- [ ] `E05-L006` Brother Anselm (arriving, warm): Miss Halloran. At nine in the morning, over my ledger. -> delivery: warm
- [ ] `E05-L021` Halloran (Edda's father) (to his daughter, loud): Edda — keep the light on me, that's all I ask of you! -> \bkeep the light on me\b
- [S] `E05-L022` Edda Halloran (to the man she calls Father, then the man she calls Father): Father, hold on. Father Anselm, hold him. -> \bhold on\b
- [ ] `E05-L023` Brother Anselm (surprised into kindness): ... I will. Carry him careful. -> \bcarry him careful\b
- [ ] `E05-L024` Delia (frightened): They'll be back for him in the morning, love. -> delivery: frightened
- [S] `E05-L029` Edda Halloran (small, to the fire): Nine months you watched me starve. -> delivery: small
- [S] `E05-L031` Edda Halloran (breaking): Then why did you not say so? -> delivery: breaking
- [ ] `E05-L033` Edda Halloran (tender, at last): I would have let you be my husband because of the gate. -> delivery: tender
- [ ] `E05-L034` Joss Marek (quiet): Then say the gate, and I'll do the paper. -> delivery: quiet
- [S] `E06-L010` Mistress Caine (last, quiet): You have made an enemy of the only family you had left. -> delivery: quiet
- [S] `E06-L011` Edda Halloran (fixed, then soft): Aunt. You were always family. Just not kind. -> delivery: soft
- [S] `E06-L016` Edda Halloran (careful): If I put my name on it, what are you then? -> delivery: careful
- [S] `E06-L018` Edda Halloran (afraid of it): That is not a small thing to be offered. -> delivery: afraid
- [S] `E06-L020` Edda Halloran (to her father, breaking): I'm looking, Father. I'm looking. -> delivery: breaking
- [S] `E06-L024` Edda Halloran (steady, first line of the season, last line too): The lamp stays lit. -> \bthe lamp stays lit\b

## long_line (corpus 25, sample 12, minimum 5)

- [S] `E01-L014` Mistress Caine (businesslike): The debt is mine, the deed is mine, the winter is mine. -> 12 words
- [ ] `E01-L022` Mistress Caine (final): Sign by the turn of the glass, or I take the lamp tonight. -> 13 words
- [ ] `E02-L005` Constable Roe (hard): Then you will answer for the ship as well as the lace. -> 12 words
- [ ] `E02-L027` Halloran (Edda's father) (drifting): The girl will not sign it, Joss. She is all I have left. -> 13 words
- [S] `E02-L030` Edda Halloran (to herself): He called me 'she' like I was a clause in the paper. -> 12 words
- [ ] `E03-L005` Edda Halloran (to Caine only): Two winters on the lamp and I will carry your coal myself. -> 12 words
- [ ] `E03-L007` Silas Vane (serious now): There is a letter here that says your father sold a ship's stores. -> 13 words
- [S] `E03-L018` Edda Halloran (measured): Then tell me what a '61 inquiry letter costs a keeper's daughter. -> 12 words
- [ ] `E03-L028` Halloran (Edda's father) (tender): If they take the lamp, they take the ten years I put in it. -> 14 words
- [S] `E04-L023` Edda Halloran (small): My father put me up here at nine and said count and don't stop. -> 14 words
- [S] `E04-L027` Edda Halloran (tender, terrified): If you touch my father's lamp you'll be standing in it, not beside it. -> 14 words
- [S] `E05-L011` Constable Roe (formal): Halloran. You will come with me for the sale of king's stores. -> 12 words
- [S] `E05-L017` Joss Marek (through the crowd): Say the '61 price out loud and see whose name it has. -> 12 words
- [ ] `E05-L021` Halloran (Edda's father) (to his daughter, loud): Edda — keep the light on me, that's all I ask of you! -> 13 words
- [S] `E05-L026` Joss Marek (at the door, not coming in): Then the lamp wants buying, and I have the money in my coat. -> 13 words
- [ ] `E05-L030` Joss Marek (unflinching): Nine months I asked Caine for one winter and she said no. -> 12 words
- [S] `E05-L032` Joss Marek (honest, ugly): Because if I was your buyer you'd have let me be your husband out of duty. -> 16 words
- [ ] `E05-L033` Edda Halloran (tender, at last): I would have let you be my husband because of the gate. -> 12 words
- [S] `E06-L002` Joss Marek (up, coat clean): Then I'll read it to the water. The water's been honest longer. -> 12 words
- [ ] `E06-L003` Joss Marek (reading): All sums owing on the lamp, the stair, the house and the keeper, now held by one Marek. -> 18 words
- [ ] `E06-L005` Joss Marek (calm): With the lace money you never saw, from the ship you wrote off. -> 13 words
- [ ] `E06-L009` Edda Halloran (clear, to all of them): Half burnt and legible still, and it has Caine's seal on the sale. -> 13 words
- [S] `E06-L010` Mistress Caine (last, quiet): You have made an enemy of the only family you had left. -> 12 words
- [ ] `E06-L015` Joss Marek (steady): It says Marek. It will say what you want it to say by the evening. -> 15 words
- [S] `E06-L019` Halloran (Edda's father) (below, on the stair, upright): Edda. Lass. I am standing on my own stair again, look at me. -> 13 words
