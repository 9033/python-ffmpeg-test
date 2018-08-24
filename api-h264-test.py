from ctypes import *
import os
import sys
sys.path.append('./libav-python')
from libav import *

class FFmpegAVFormatContext(Structure):
    _fields_ = [
        ('context', POINTER(AVFormatContext))
    ]

def h264_test(): #api-h264-test.c
    fmt_ctx =FFmpegAVFormatContext() #ctx=POINTER(AVFormatContext) is not working

    ret=avformat.avformat_open_input(byref(fmt_ctx.context),b"F:\\myfile\\idlogo.mp4",None,None)
    #ret=avformat.avformat_open_input(byref(fmt_ctx.context),b"F:\\myfile\\intro.010.png",None,None)

    ret=avformat.avformat_find_stream_info(fmt_ctx.context, None)

    video_stream=avformat.av_find_best_stream(fmt_ctx.context,AVMEDIA_TYPE_VIDEO, -1, -1, None, 0)

    origin_par = fmt_ctx .context[0].streams[video_stream][0].codecpar

    codec = avcodec.avcodec_find_decoder(origin_par[0].codec_id)

    ctx=avcodec.avcodec_alloc_context3(codec)

    ret=avcodec.avcodec_parameters_to_context(ctx,origin_par)

    ret=avcodec.avcodec_open2(ctx,codec,None)

    fr=avutil.av_frame_alloc()

    byte_buffer_size=avutil.av_image_get_buffer_size(ctx[0].pix_fmt,ctx[0].width,ctx[0].height,16)

    byte_buffer=avutil.av_malloc(byte_buffer_size)
    
    print('video',video_stream, fmt_ctx.context[0].streams[video_stream][0].time_base.num, fmt_ctx.context[0].streams[video_stream][0].time_base.den)
    
    pkt=AVPacket()
    avcodec.av_init_packet(byref(pkt))

    end_of_stream=0
    got_frame=0
    i=0

    while True: #do..while is do not appear in python
        if(not end_of_stream):
            if(avformat.av_read_frame(fmt_ctx.context, byref(pkt)) < 0):                
                end_of_stream=1            
        if(end_of_stream):
            pkt.data=None
            pkt.size=0
        if ((pkt.stream_index == video_stream) or end_of_stream):
            got_frame=0            
            if(pkt.pts==AV_NOPTS_VALUE):
                pkt.pts=pkt.dts=i
            got_frame_c=c_int()
            ret=avcodec.avcodec_decode_video2(ctx,fr,byref(got_frame_c),byref(pkt))
            got_frame=got_frame_c.value
            if(ret<0):
                print("avcodec_decode_video2",ret)
                return
            if(got_frame):

                c_uint8_p=POINTER(c_uint8)
                byte_buffer_uint8_p=cast(byte_buffer,c_uint8_p)

                fr_data=(POINTER(c_uint8)*4)()
                fr_data[0]=fr[0].data[0]
                fr_data[1]=fr[0].data[1]
                fr_data[2]=fr[0].data[2]
                fr_data[3]=fr[0].data[3]

                fr_linesize=(c_int*4)()
                fr_linesize[0]=fr[0].linesize[0]
                fr_linesize[1]=fr[0].linesize[1]
                fr_linesize[2]=fr[0].linesize[2]
                fr_linesize[3]=fr[0].linesize[3]
                
                number_of_written_bytes=avutil.av_image_copy_to_buffer(byte_buffer_uint8_p,byte_buffer_size,
                fr_data, fr_linesize,
                ctx[0].pix_fmt,ctx[0].width,ctx[0].height,1)
                if(number_of_written_bytes<0):
                    print("av_image_copy_to_buffer")
                    return
                print(video_stream,
                        fr[0].pts, fr[0].pkt_dts, fr[0].pkt_duration,
                        number_of_written_bytes, hex(avutil.av_adler32_update(0, byte_buffer_uint8_p, number_of_written_bytes)))
            avcodec.av_packet_unref(byref(pkt))
            avcodec.av_init_packet(byref(pkt))
        i+=1            
        
        if(not (not end_of_stream or got_frame)):break
        
    avcodec.av_packet_unref(byref(pkt))
    avutil.av_frame_free(byref(fr))
    avcodec.avcodec_close(ctx)
    avformat.avformat_close_input(byref(fmt_ctx.context))
    avcodec.avcodec_free_context(byref(ctx))
    avutil.av_freep(byref(byte_buffer_uint8_p))


'''
run main
'''

if __name__=='__main__':
    h264_test()