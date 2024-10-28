import cv2
from django.shortcuts import render
from .forms import UploadImageForm
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

class Cartoonizer:
    def render(self, img_rgb_path):
        img_rgb = cv2.imread(img_rgb_path)
        img_rgb = cv2.resize(img_rgb, (1366, 768))
        numDownSamples = 2  # number of downscaling steps
        numBilateralFilters = 50  # number of bilateral filtering steps

        # -- STEP 1 --
        img_color = img_rgb
        for _ in range(numDownSamples):
            img_color = cv2.pyrDown(img_color)

        # Apply bilateral filter
        for _ in range(numBilateralFilters):
            img_color = cv2.bilateralFilter(img_color, 9, 9, 7)

        # Upsample image
        for _ in range(numDownSamples):
            img_color = cv2.pyrUp(img_color)

        # -- STEP 2 --
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        img_blur = cv2.medianBlur(img_gray, 3)

        # -- STEP 3 --
        img_edge = cv2.adaptiveThreshold(img_blur, 255,
                                         cv2.ADAPTIVE_THRESH_MEAN_C,
                                         cv2.THRESH_BINARY, 9, 2)

        # -- STEP 4 --
        (x, y, z) = img_color.shape
        img_edge = cv2.resize(img_edge, (y, x))
        img_edge = cv2.cvtColor(img_edge, cv2.COLOR_GRAY2RGB)

        return cv2.bitwise_and(img_color, img_edge)

def upload_image(request):
    if request.method == 'POST':
        form = UploadImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            fs = FileSystemStorage()

            # Save the uploaded file
            file_path = os.path.join(settings.MEDIA_ROOT, fs.save(image.name, image))

            # Apply cartoon effect
            cartoonizer = Cartoonizer()
            cartoon_image = cartoonizer.render(file_path)

            # Save the cartoon image
            cartoon_image_path = os.path.join(settings.MEDIA_ROOT, 'cartoon_image.jpg')
            cv2.imwrite(cartoon_image_path, cartoon_image)

            return render(request, 'result.html', {'cartoon_image_url': fs.url('cartoon_image.jpg')})

    else:
        form = UploadImageForm()

    return render(request, 'upload.html', {'form': form})
