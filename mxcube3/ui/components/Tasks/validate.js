const everpolate = require('everpolate');

const validate = (values, props) => {
  const errors = {};
  if (!props.motorLimits.resolution) {
    // for some reason redux-form is loaded before the initial status @##@!
    return errors;
  }
  const currEnergy = parseFloat(values.energy);
  const currRes = parseFloat(values.resolution);
  const energies = props.motorLimits.resolution.limits.map(value => value[0]);
  const limitsMin = props.motorLimits.resolution.limits.map(value => value[1]);
  const limitsMax = props.motorLimits.resolution.limits.map(value => value[2]);
  // here we update the resolution limits based on the energy the typed in the form,
  // the limits come from a table sent by the client
  const resMin = everpolate.linear(currEnergy, energies, limitsMin);
  const resMax = everpolate.linear(currEnergy, energies, limitsMax);

  if (values.num_images === '' ||
      parseInt(values.num_images, 10) > props.acqParametersLimits.number_of_images) {
    errors.num_images = 'Number of images above the limit';
  }
  if (values.osc_range === '') {
    errors.osc_range = 'field empty';
  }
  if (values.osc_start === '') {
    errors.osc_start = 'field empty';
  }
  if (values.exp_time === '' || values.exp_time > props.acqParametersLimits.exposure_time) {
    errors.exp_time = 'Exposure time above the limit';
  }
  if (!(currRes > resMin && currRes < resMax)) {
    errors.resolution = 'Resolution outside working range';
  }
  if (!(currEnergy > props.motorLimits.energy.limits[0] &&
        currEnergy < props.motorLimits.energy.limits[1])) {
    errors.energy = 'Energy outside working range';
  }
  if (values.osc_range === '' || values.osc_range > props.acqParametersLimits.osc_range) {
    errors.osc_range = 'Oscillation range outside the limit';
  }
  return errors;
};

export default validate;
