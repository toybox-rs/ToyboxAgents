from glob import glob
import cv2

if __name__ == "__main__":
    agent = "VelocityEstimate"
    imglst = glob("./outputs/{}*.png".format(agent))
    imglst = sorted(imglst)
    frames = [cv2.imread(img) for img in imglst]
    height, width, layers = frames[0].shape

    video_name = './outputs/{}.avi'.format(agent)
    video = cv2.VideoWriter(video_name, 0, 30, (width, height))

    for image in frames:
        video.write(image)

    cv2.destroyAllWindows()
    video.release()