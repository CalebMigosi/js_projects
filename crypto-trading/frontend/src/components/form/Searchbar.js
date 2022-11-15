import React, {Component, createRef} from "react";
import styled from "styled-components";
import SearchImage from "../../assets/img/search.svg"
export default class SearchBar extends Component{
    constructor(props){
        super(props)
        this.state = {
            barOpened: false,
            input:""
        }

        this.formRef = createRef()
        this.inputFocus = createRef()
    }
    
    onFormSubmit(e){
        e.preventDefault();

        console.log(e.target[1].value)
        // Set state of input 
        this.setState({input: ""})
        this.setState({barOpened: false})
        this.inputFocus.current.blur()
    }

    render(){
        return (
            <Form barOpened={this.state.barOpened}
                onClick = {() => {
                    this.setState({ barOpened: !this.state.barOpened })
                    this.inputFocus.current.focus()
                }}
                
                onBlur = {()=>{
                    this.setState({barOpened: false})
                }}

                onSubmit ={(e) =>{this.onFormSubmit(e)}}
                ref={this.formRef}
                >
                    
            <Button type="submit"><Image src={SearchImage}></Image></Button>
            <Input
                // Update input state
                onChange = {e => this.setState({input: e.target.value})}
                ref = {this.inputFocus}
                value ={this.state.input}
                barOpened = {this.state.barOpened}
                placeholder=" Search for a security"
                />
            </Form>
        )
    }
}

const Form = styled.form`
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2 );
    background-color: #145da0;
    
    // Change width if bar is opened
    width: ${props => (props.barOpened ? "30rem" : "1.5rem")};

    // Change pointer if bar opened as well
    cursor: ${props => (props.barOpened ? "auto" : "pointer")};
    padding: 0.3rem;
    height: 2vh;
    border-radius: 10rem;
    transition: width 300ms cubic-bezier(0.645, 0.045, 0.355, 1);
`


const Input = styled.input`
  font-size: 14px;
  line-height: 1;
  background-color: transparent;
  width: ${props => (props.barOpened ? "100%" : "0%")};
  margin-left: ${props => (props.barOpened ? "1rem" : "0rem")};
  border: none;
  color: white;
  transition: margin 300ms cubic-bezier(0.645, 0.045, 0.355, 1);

  &:focus,
  &:active {
    outline: none;
  }
  &::placeholder {
    color: white;
  }
`;

const Button = styled.button`
  line-height: 1;
  pointer-events: ${props => (props.barOpened ? "auto" : "none")};
  cursor: ${props => (props.barOpened ? "pointer" : "none")};
  background-color: transparent;
  border: none;
  outline: none;
  color: white;
`;

const Image = styled.img`
  height: 1.2rem;
  width: 1.2rem;
`

Image.defaultProps = {
    src: SearchBar
}