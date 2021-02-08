from perlin_noise import PerlinNoise
import math
noise = PerlinNoise(octaves = 1, seed = 5856154)
for i in range(101):
    print(math.floor(-1 * noise(i/10)) + 1)