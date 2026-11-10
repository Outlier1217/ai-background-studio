
from services.background_remover import background_remover

result = background_remover.process_first_frame(
    video_path="storage/uploads/test-video.mp4",
    output_path="storage/processed/transparent.png",
)

print("\nAI PROCESSING RESULT")
print(result)
