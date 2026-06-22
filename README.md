# mtcaptcha-solver
<img width="794" height="229" alt="image" src="https://github.com/user-attachments/assets/508c1f1d-a9e1-46cd-9671-8899978c7822" />

# deobfuscation process 
I started by using the demo found on the [2captcha](https://2captcha.com/demo/mtcaptcha) website - when analysing the network requests this is what we see:

<img width="425" height="314" alt="image" src="https://github.com/user-attachments/assets/801b59fd-b9bb-4014-bc80-e2737fd1ed2a" />

The first request (one highlighted in pink) is a GET request being made to mtcaptcha which fetches the actual captcha js and its also the code for the iframe itself, after that this js calls the "mtcv1/api/getchallenge.json" endpoint (highlighted in orange) and from that we get a challenege issued by the server for the js to solve, once the challenege is computed we use that to fetch the image (highlighted in yellow) by calling "/getimage.json" - once the image is read using a OCR model (in our case ive used deepinfra's api using the qwen model, this is just for simplicity feel free to use a local ocr or even train your own for cheaper and faster results) - and then we submit the answer, `fa`, `kt`, and `fs` (original fseed) to solvechallenge.json (highlighted in green) which gives you a `vt` (verification token) which can be checked using 2captchas verify endpoint.

As for the JS itself the obfuscation is rather minimal, most of it is string obfuscation, we see that `function _0x27c6()` is where all the strings are stored:

<img width="556" height="445" alt="image" src="https://github.com/user-attachments/assets/a789d25d-c5b1-491c-a141-18045d87e4c4" />

And there is a rotator which determines the correct index needed for each place this function is called:

<img width="571" height="202" alt="image" src="https://github.com/user-attachments/assets/f01f52ec-43c2-499a-befc-43ba5fa2254b" />

Once that is indentified bable was used to automatically replace all instances of this to the actual value from the string table - for example:
```
Math[_0x5839(0x2e3)](
    Date[_0x5839(0x2a9)]()
)
```
turns into:
```Math.floor(Date.now())```

Once this was done with the others, we then found the initiale fold that is responsible for completeing the first challenege (the one we need to complete in order to get the iamge) - and we can see that here: 
```
FoldChlg: {
  URLSafeBase64CharCode2IntMap: [...],
  URLSafeBase64Int2CharMap: [...],
  solve: function (...) { ... },
  foldBase64IntArray: function (...) { ... },
  ...
}
```
What the fold is doing is this:
1. Decode the seed into an array of integers (0‑63) using the URL‑safe base64 alphabet
2. Repeat `fslots` times:
  1. Apply foldBase64IntArray 31 times.
  2. Apply the same fold operation fdepth times on the result.
  3. Hash the array using hashIntAry (a 32‑bit signed integer hash).
  4. Take the hash modulo 4096 and encode it as two base64 characters (since 4096 = 64²).
  5. Append those two chars to the output.

Return the concatenated string – this is `fa` - and without this the server rejects the request to actually get the image. 

after this we send it to `/solvechallenge.json` using the following parameters:

| Parameter | Description                                                               |
| --------- | ------------------------------------------------------------------------- |
| `ct`      | The challenge token obtained from the initial challenge request.          |
| `st`      | The CAPTCHA solution (text read from the CAPTCHA image).                  |
| `fa`      | The fold answer (proof-of-work value computed from the fold seed).        |
| `kt`      | Keystroke data used to simulate user typing behavior.                     |
| `fs`      | The original fold seed returned by the challenge endpoint.                |
| `lf`      | Indicates whether the challenge is low-friction (`0` = normal challenge). |
| `sk`      | The site key associated with the CAPTCHA instance.                        |
| `bd`      | The domain on which the CAPTCHA is being solved.                          |
| `rt`      | Request timestamp in milliseconds since the Unix epoch.                   |
| `tsh`     | Transaction signature: `TH[MD5("mtcap@mtcaptcha.com" + sitekey)]`.        |
| `ss`      | Session identifier generated for each solve attempt.                      |



