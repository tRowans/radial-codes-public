# inspired by https://github.com/oscarhiggott/stimbposd/blob/main/src/stimbposd/sinter_bp_osd.py
import pathlib
from typing import Dict
import numpy as np
from sinter import Decoder, CompiledDecoder
import stim
from .bposd_overlapping_window import BpOsdOverlappingWindowDecoder


class SinterCompiledDecoder_OWD_Base(CompiledDecoder):
    """A generic class for sinter simulation of decoding stim circuits using the overlapping window approach using a
    sinter compiled decoder that is instantiated using a DEM.

    Args:decoder: The decoder to be used for decoding. This decoder has to implement the `decode_batch` method.
    """

    def __init__(self, decoder):
        self.decoder = decoder

    def decode_shots_bit_packed(
        self,
        *,
        bit_packed_detection_event_data: np.ndarray,
    ) -> np.ndarray:
        return self.decoder.decode_batch(
            shots=bit_packed_detection_event_data,
            bit_packed_shots=True,
            bit_packed_predictions=True,
        )


class SinterDecoder_Base_OWD(Decoder):
    def __init__(
        self,
        Decoder_cls,  # should be class compatible with SinterCompiledDecoder_OWD_Base
        **decoder_kwargs,
    ):
        self.Decoder_cls = Decoder_cls
        self.decoder_kwargs = decoder_kwargs

    def compile_decoder_for_dem(
        self, *, dem: stim.DetectorErrorModel
    ) -> CompiledDecoder:
        return SinterCompiledDecoder_OWD_Base(
            self.Decoder_cls(dem, **self.decoder_kwargs)
        )

    def decode_via_files(
        self,
        *,
        num_shots: int,
        num_dets: int,
        num_obs: int,
        dem_path: pathlib.Path,
        dets_b8_in_path: pathlib.Path,
        obs_predictions_b8_out_path: pathlib.Path,
        tmp_dir: pathlib.Path,
    ) -> None:
        """Performs decoding by reading problems from, and writing solutions to, file paths.
        Args:
            num_shots: The number of times the circuit was sampled. The number of problems
                to be solved.
            num_dets: The number of detectors in the circuit. The number of detection event
                bits in each shot.
            num_obs: The number of observables in the circuit. The number of predicted bits
                in each shot.
            dem_path: The file path where the detector error model should be read from,
                e.g. using `stim.DetectorErrorModel.from_file`. The error mechanisms
                specified by the detector error model should be used to configure the
                decoder.
            dets_b8_in_path: The file path that detection event data should be read from.
                Note that the file may be a named pipe instead of a fixed size object.
                The detection events will be in b8 format (see
                https://github.com/quantumlib/Stim/blob/main/doc/result_formats.md ). The
                number of detection events per shot is available via the `num_dets`
                argument or via the detector error model at `dem_path`.
            obs_predictions_b8_out_path: The file path that decoder predictions must be
                written to. The predictions must be written in b8 format (see
                https://github.com/quantumlib/Stim/blob/main/doc/result_formats.md ). The
                number of observables per shot is available via the `num_obs` argument or
                via the detector error model at `dem_path`.
            tmp_dir: Any temporary files generated by the decoder during its operation MUST
                be put into this directory. The reason for this requirement is because
                sinter is allowed to kill the decoding process without warning, without
                giving it time to clean up any temporary objects. All cleanup should be done
                via sinter deleting this directory after killing the decoder.
        """
        dem = stim.DetectorErrorModel.from_file(dem_path)
        decoder = self.Decoder_cls(dem, **self.decoder_kwargs)
        shots = stim.read_shot_data_file(
            path=dets_b8_in_path,
            format="b8",
            num_detectors=dem.num_detectors,
            bit_packed=False,
        )
        predictions = decoder.decode_batch(shots)
        stim.write_shot_data_file(
            data=predictions,
            path=obs_predictions_b8_out_path,
            format="b8",
            num_observables=dem.num_observables,
        )


class SinterDecoder_BPOSD_OWD(SinterDecoder_Base_OWD):
    def __init__(
        self,  # should be class compatible with SinterCompiledDecoder_OWD_Base
        **decoder_kwargs,
    ):
        super().__init__(BpOsdOverlappingWindowDecoder, **decoder_kwargs)
