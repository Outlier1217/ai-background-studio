
from services.video_processor import video_processor

result = video_processor.process_video(
    input_path="storage/uploads/test-video.mp4",
    background_path="storage/backgrounds/test-background.jpg",
    output_path="storage/processed/final-video.mp4",
)

print("\nVIDEO PROCESSING COMPLETED!")
print(result)
