# Diffusion Illusion Technique Explained

This document is a long-form explanation of the technique behind the original Diffusion Illusions workflow and the Rubik-specific version in this repo.

It is written for readers who want a conceptual explanation first and code details second.

Use this together with:

- [`docs/current-status.md`](./current-status.md)
- [`docs/rubiks-diffusion-illusion-plan.md`](./rubiks-diffusion-illusion-plan.md)
- [`experiments/local-face-sweep/run_local_face_sweep.py`](../experiments/local-face-sweep/run_local_face_sweep.py)
- [`python_bridge/rubiks_illusion_torch.py`](../python_bridge/rubiks_illusion_torch.py)

## The Short Version

Normal Stable Diffusion generation starts from random noise and denoises it into one image for one prompt.

Diffusion Illusions does something different:

- keep the pretrained Stable Diffusion model fixed
- define some **learnable source images**
- define one or more deterministic ways to transform those source images into **derived views**
- use Stable Diffusion as a differentiable critic that says how each derived view should change to better match its prompt
- backpropagate that signal into the shared source images

The result is not a single generated image from scratch. The result is a set of source images that have been optimized so that multiple transformed views all look meaningful at once.

That shared-source requirement is the heart of the technique.

## Why This Technique Exists

The interesting problem is not "can a diffusion model make a good-looking image from a prompt?"

Stable Diffusion already does that.

The interesting problem is:

- can we find one hidden representation
- such that several different transformed outputs
- all look like intended images
- even though those outputs share the same underlying source content

In the original Diffusion Illusions setup, the shared thing is a source image or texture and the different outputs are transformations or views of it.

In this Rubik project, the shared thing is six source face images and the different outputs are the solved and scrambled cube faces rendered from those six images.

## Normal Stable Diffusion Generation

To understand Diffusion Illusions, it helps to contrast it with normal Stable Diffusion inference.

### What Happens In Ordinary Generation

At a high level, normal Stable Diffusion generation does this:

1. Encode the prompt into text embeddings.
2. Start from random latent noise.
3. Repeatedly ask the denoising network what noise to remove at each timestep.
4. Use the scheduler to move from a noisier latent to a cleaner one.
5. Decode the final latent into an RGB image.

This is image **generation by inference**.

The model already knows how to do this because it was trained beforehand on a huge corpus of image-text pairs.

### Why No Learning Is Needed During Generation

No learning happens during normal prompt-to-image use because the model weights are already trained.

You are not teaching the model new concepts in that moment. You are asking the already-trained model to produce one sample that matches the prompt.

In other words:

- training the model happened long before you ran it
- inference is just using the learned model

## The Main Stable Diffusion Components

Three components matter most for understanding this project.

### Text Encoder

The text encoder converts a prompt like:

```text
a watercolor drawing of a cute cat
```

into a tensor of numbers that represents the prompt's meaning in a form the diffusion model can use.

In the reused Diffusion-Illusions code, this happens in `get_text_embeddings(...)` in the official `source/stable_diffusion.py`.

### VAE

The VAE is the image compressor/decompressor used by Stable Diffusion.

It does two jobs:

- encode an RGB image into a smaller latent representation
- decode a latent representation back into an RGB image

Stable Diffusion mostly operates in latent space because that is cheaper than working directly in full-resolution RGB space.

### U-Net

The U-Net is the core denoising network.

It takes:

- the current noisy latent
- the current timestep
- the text embeddings

and predicts the noise content of that latent.

In normal image generation, this prediction is used to gradually denoise a random latent into a prompt-matching image.

## What Diffusion Illusions Changes

Diffusion Illusions does **not** use Stable Diffusion only as a generator.

Instead, it uses the pretrained model as a source of gradients.

The core change is:

- do not start from random noise and sample one final image
- instead, maintain a set of learnable source images
- transform them into one or more derived views
- ask Stable Diffusion how those views should change to better match prompts
- update the shared source images accordingly

This is not fine-tuning Stable Diffusion itself.

The pretrained Stable Diffusion model stays fixed. The thing being optimized is the input-side representation.

## The General Pattern

A Diffusion Illusions-style loop usually looks like this:

1. Create learnable source images.
2. Transform them into one or more derived images using a deterministic operator.
3. Pair those derived images with prompts.
4. Feed a derived image and its prompt into a diffusion-based loss step.
5. Backpropagate the resulting gradient into the source images.
6. Update the source images with an optimizer such as SGD or Adam.
7. Repeat.

The source images are the persistent state across iterations.

The derived views are temporary projections of that shared state.

## The Key Insight: Shared Sources Matter More Than Individual Views

This is the most important conceptual point.

If you generate or denoise one derived view at a time, each view can look individually plausible while still being **mutually inconsistent** with the others.

That happens because each derived view only reveals part of the hidden source state.

Several different source-image configurations can produce a believable-looking derived view. So if you optimize views independently, different views can silently imply contradictory underlying source pixels.

That means:

- a pretty `view A` does not uniquely determine the hidden source
- a pretty `view B` does not uniquely determine the hidden source either
- the two "good-looking" views can disagree about what the shared source must be

This is why the optimization target cannot be "make one rendered view nice."

The true target is:

- find a single shared source representation
- whose many rendered views all become good together

That is why gradient-based optimization over shared parameters is so useful here.

## Why Simple Per-View Generation Is Not Enough

Suppose you tried a simpler method:

1. render one current derived view
2. run a normal denoising or img2img step on that view with its prompt
3. somehow write the improved view back into the source images

The problem is step 3.

There is usually no clean inverse map from a derived view back to the full shared source representation.

Even when a partial inverse exists, it often creates conflicts:

- one view wants source region X to look one way
- another view wants the same shared source region to look another way

If you optimize each view in isolation, those conflicts are hidden until you compare all views together.

The Diffusion Illusions approach solves this by always updating the **same shared source parameters** directly.

## What `train_step(...)` Is Doing Conceptually

The reused Diffusion-Illusions `StableDiffusion.train_step(...)` method is the critical bridge between a rendered view and a gradient signal.

It is not generating a final image.

It is computing "how should this current image change so that Stable Diffusion thinks it fits the prompt better?"

At a high level, it does this:

1. Take the current predicted RGB image.
2. Resize it to the expected Stable Diffusion input size.
3. Encode it into latent space with the VAE.
4. Sample a diffusion timestep.
5. Add known random noise to the latent.
6. Ask the U-Net to predict the noise, conditioned on the prompt.
7. Compare the predicted noise to the actual sampled noise.
8. Turn that comparison into a gradient.
9. Backpropagate that gradient into the original image.

In the official code, the central quantity is:

```python
noise_delta = noise_pred - noise
```

The rough interpretation is:

- `noise` is the actual corruption that was added
- `noise_pred` is what the prompt-conditioned diffusion model thinks the noise should look like
- the difference between them tells us how the latent, and therefore the image, should move

The returned value is not the important thing.

The important effect is the backward pass.

## Why `noise_pred - noise` Gives A Useful Signal

Stable Diffusion has already learned a large prior over what images matching text prompts tend to look like.

When we take the current image, add noise, and ask the U-Net to predict that noise:

- if the image fits the prompt well, the prompt-conditioned denoising behavior is more compatible with the latent
- if the image does not fit the prompt well, the prompt-conditioned prediction will pull in a different direction

That directional mismatch becomes the training signal.

So the model is effectively telling us:

- "for this prompt, a latent like this should denoise differently"
- "move your current image in that direction"

This is why Stable Diffusion behaves like a differentiable critic in this setup rather than a normal image generator.

## What Is Being Trained In This Repo

In this project, the trainable object is not the Stable Diffusion model.

The trainable object is the set of six Rubik face images:

- `U`
- `D`
- `L`
- `R`
- `F`
- `B`

The current maintained runner is:

- [`experiments/local-face-sweep/run_local_face_sweep.py`](../experiments/local-face-sweep/run_local_face_sweep.py)

It uses the official Diffusion-Illusions repo for:

- `source/stable_diffusion.py`
- `source/learnable_textures.py`
- prompt-label helpers

But it replaces the official geometry/operator side with this repo's Rubik-specific renderer.

## The Rubik-Specific Arrangement Operator

This repo's differentiable arrangement operator is implemented in:

- [`python_bridge/rubiks_illusion_torch.py`](../python_bridge/rubiks_illusion_torch.py)

That operator takes the six current source face images and deterministically renders:

- the six solved visible faces
- the six scrambled visible faces

Each derived visible face is built by:

- selecting tiles from the source faces
- rotating those tiles as required
- stitching them into a 3x3 face image

That means the hidden variables are the six source faces, while the observed training targets are many derived views of those same faces.

## How The Rubik Workflow Runs

The maintained sweep follows this pattern:

1. Create six learnable face images using `LearnableImageFourier`.
2. Render solved and scrambled views from those faces with the Rubik operator.
3. Sample one training view such as `solved:R` or `scrambled:U`.
4. Call `stable_diffusion.train_step(...)` on that rendered view and its prompt.
5. Let the gradient flow back through the Rubik renderer into the six source faces.
6. Run `optimizer.step()` to update the six source faces.
7. Repeat for many iterations.

The current best-known setup is intentionally close to the official Diffusion Illusions notebooks, but uses smaller image/feature sizes to fit the Rubik problem into practical GPU memory.

## Why The Learned Faces Are The Final Output

It can feel surprising that the project is "learning images" rather than "generating images," because the final outputs are still PNGs.

The distinction is about **how** those PNGs are obtained.

Normal generation:

- start from random noise
- run the pretrained model forward
- get one sample

This project:

- start from learnable source-face parameters
- optimize them over many iterations using diffusion gradients
- save the final optimized source faces and their rendered solved/scrambled views

So the end result is still images, but they are optimized images, not one-shot generated samples.

## Why ComfyUI Is Not A Drop-In Replacement

Standard ComfyUI usage is centered on inference workflows:

- load a checkpoint
- wire together prompt, sampler, VAE, ControlNet, LoRA, and output nodes
- produce images

That is a great fit for normal Stable Diffusion generation.

It is not a direct fit for this project because this project needs:

- persistent learnable parameters for six source images
- a custom differentiable Rubik renderer in the loop
- backpropagation through the rendered views into the shared source images
- optimizer steps over many iterations

ComfyUI could only host this if we wrapped the whole optimization loop in custom code or custom nodes.

At that point, ComfyUI would just be a shell around a custom PyTorch training system rather than the core solution.

## Pseudocode For The Full Idea

```python
source_faces = initialize_learnable_faces()
optimizer = SGD(source_faces.parameters())

for iteration in range(num_iterations):
    optimizer.zero_grad()

    rendered_views = rubik_renderer(source_faces)
    sampled_view = choose_one_training_view(rendered_views)

    stable_diffusion.train_step(
        text_embeddings=sampled_view.prompt_embedding,
        pred_rgb=sampled_view.image,
        guidance_scale=guidance_scale,
        noise_coef=noise_coef,
    )

    optimizer.step()
```

The missing detail in that pseudocode is the key one:

`train_step(...)` is not just returning a score. It is producing gradients that flow all the way back into `source_faces`.

## What Makes The Rubik Version Interesting

This repo turns the general Diffusion Illusions idea into a stronger consistency problem than a single transformed image.

The hidden state is not one image but six coordinated face images.

The derived outputs are not arbitrary crops but cube faces produced by a fixed scramble mapping with tile rotations.

So the system has to find source-face content that remains semantically useful after:

- tile permutation
- tile rotation
- view selection
- switching between solved and scrambled arrangements

That makes the shared-source constraint especially important.

## Practical Takeaways

- The pretrained Stable Diffusion model is reused as a fixed source of semantic gradients.
- The project is training the six source face images, not fine-tuning Stable Diffusion.
- The real problem is multi-view consistency under a shared hidden source.
- A separately generated pretty view is not enough if it cannot be reconciled with the same shared source images.
- The phrase to keep in mind is: individually plausible views can still be mutually inconsistent.

That is the reason the project uses a shared optimization loop instead of independent per-view generation.
