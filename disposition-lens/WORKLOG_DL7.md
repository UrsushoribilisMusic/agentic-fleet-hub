# DL-7 Worklog — Dog-avatar face: expressive dog replacing/augmenting the smiley (7 dispositions)

**Context:** Apertus hackathon consumer direction (on-brand: Miguel's dog Bunny, agent Dev Groar).  
**Goal:** Replace/augment the porthole smiley with an expressive dog that conveys the 7 dispositions, kept parametric off the same `STATES` map + tweened parameters so the signal pipeline remains unchanged. Add an avatar toggle (Dog <-> Smiley) for video A/B testing.

## Implementation Details

1. **Parametric Dog Avatar (`DogFace` component):**
   - **Ears:** Fully articulated left and right ears with per-disposition rotation angles (`earL`, `earR`) and vertical displacement (`earY`), plus inner ear shading reacting to disposition tint.
   - **Head Tilt (`headTilt`):** Head rotates around its center `(150, 155)` dynamically (crucial for inquisitive `curious` [-10°] and puzzled `uncertain` [+13°] dog expressions).
   - **Eyebrows (`browY`, `browAng`):** Expressive dog brow markings that furrow or raise.
   - **Eyes (`eyeOpen`, `pupilX`, `pupilY`, `blink`):** Large friendly eyes with dual specular catchlights; happy squint crescents on `warm` (`eyeOpen <= 0.55`); looking askance on `uncertain` and down on `reluctant`.
   - **Snout & Muzzle:** Dedicated snout patch, nose with highlight specular reflection, philtrum, and whisker spots.
   - **Mouth & Tongue (`mouth`, `tongue`):**
     - `warm`: Wide open happy panting smile with articulated pink tongue and crease (`tongue: 1.0`).
     - `confident`: Smirk with subtle playful tongue tip (`tongue: 0.35`).
     - `curious`: Soft parted mouth with gentle tongue tip (`tongue: 0.15`).
     - `uncertain`: Quizzical wavy closed mouth.
     - `concern`: Tense open oval mouth.
     - `reluctant`: Downturned pout/frown.
     - `idle`: Gentle closed classic 'w' dog lips.
   - **Chest Bib & Brass Collar:** Submarine-themed chest contour with brass collar band and medallion.
   - **Bunny Eye Patch:** Distinctive marking patch over the left eye for Dev Groar / Bunny character.

2. **Avatar Toggle & UI Controls:**
   - Added a 2-option grid selector: `[ 🐶 Dog (Bunny) ]` and `[ 🙂 Smiley ]`.
   - Defaults to `dog` while preserving the classic `Face` smiley for seamless A/B recording.
   - Provenance footer updated to reflect the active avatar state.

3. **Build & Verification:**
   - Executed `prototype/build.sh` to generate the self-contained `prototype/standalone.html`.
   - Validated Babel classic runtime transform in Node without runtime or syntax errors.
   - Verified that all 60 Python unit tests pass cleanly.
